import os
import re

import pandas as pd
from Bio import SeqIO
from dotenv import load_dotenv

from ..config.celery import celery_app
from .plasticome_metadata_service import get_all_enzymes

load_dotenv(override=True)


def get_cazy_info():
    """
    The function `get_cazy_info` retrieves information about enzymes and returns a
    set of CAZy family names.
    :return: a set of cazy_family values extracted from the database.
    """
    enzymes_info, error = get_all_enzymes(
        os.getenv('PLASTICOME_USER'), os.getenv('PLASTICOME_PASSWORD')
    )
    if error:
        return set()
    return set(item['cazy_family'] for item in enzymes_info)


def get_ec_numbers_info():
    """
    The function `get_ec_numbers_info` retrieves information about enzymes and
    returns a set of their EC numbers.
    :return: a set of EC numbers.
    """
    enzymes_info, error = get_all_enzymes(
        os.getenv('PLASTICOME_USER'), os.getenv('PLASTICOME_PASSWORD')
    )
    if error:
        return set()
    return set(item['ec_number'] for item in enzymes_info)


cazy_info_set = get_cazy_info()
ec_info_set = get_ec_numbers_info()


def check_ec_numbers(ec_numbers: str):
    """
    The function checks if any of the EC numbers in a given string are present in a
    set, and returns the first matching number or False if none are found.

    :param ec_numbers: The `ec_numbers` parameter is a string that contains EC
    numbers separated by '|'
    :type ec_numbers: str
    :return: either True, a specific EC number, or False.
    """
    if len(ec_info_set) < 1:
        return True

    for number in str(ec_numbers).split('|'):
        if number in ec_info_set:
            return number
    return False


def check_cazy(families: str):
    """
    The function "check_cazy" checks if any of the families in the input string are
    present in a set called "cazy_info_set".

    :param families: A string representing a list of families. Each family is
    separated by a "+" sign
    :type families: str
    :return: a boolean value. It returns True if any of the families in the input
    string are present in the cazy_info_set, and False otherwise.
    """
    if len(cazy_info_set) < 1:
        return True

    for family in str(families).split('+'):
        family = re.sub(r'\(.*\)', '', family)
        if family in cazy_info_set:
            return family
    return False


def get_first_non_false(row):
    """
    The function returns the first non-false value from a given row, prioritizing
    the 'HMMER' value, then 'eCAMI', then 'DIAMOND', and returning False if all
    values are false.

    :param row: The parameter `row` is expected to be a dictionary-like object that
    contains the keys `'HMMER'`, `'eCAMI'`, and `'DIAMOND'`. Each of these keys is
    expected to have a corresponding value that can be evaluated as a boolean
    (e.g., `True
    :return: the value of the first non-false element in the row. If none of the
    elements are non-false, it will return False.
    """
    if row['HMMER'] != False:
        return row['HMMER']
    elif row['eCAMI'] != False:
        return row['eCAMI']
    elif row['DIAMOND'] != False:
        return row['DIAMOND']
    else:
        return False


@celery_app.task
def dbcan_result_filter(dbcan_result: tuple):
    absolute_dir, _ = dbcan_result
    dbcan_files_to_delete = [
        'diamond.out',
        'hmmer.out',
        'eCAMI.out',
        'uniInput',
    ]

    try:
        for filename in os.listdir(absolute_dir):
            if filename.endswith('.faa'):
                protein_file_path = os.path.join(absolute_dir, filename)

            for file in dbcan_files_to_delete:
                file_path = os.path.join(absolute_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)

        enzymes = pd.read_csv(
            os.path.join(absolute_dir, 'overview.txt'), sep='\t'
        )
        enzymes[['HMMER', 'eCAMI', 'DIAMOND']] = enzymes[
            ['HMMER', 'eCAMI', 'DIAMOND']
        ].map(check_cazy)
        enzymes['plasticome_cazyme'] = enzymes.apply(
            get_first_non_false, axis=1
        )
        enzymes['in_db'] = enzymes['plasticome_cazyme'].apply(
            lambda cazy: True if cazy else False
        )
        gene_ids_to_keep = enzymes.loc[enzymes['in_db'], 'Gene ID'].tolist()

        enzymes['EC#'] = enzymes['EC#'].map(check_ec_numbers)

        enzymes = enzymes.drop(
            columns=['#ofTools', 'HMMER', 'eCAMI', 'DIAMOND', 'in_db']
        )
        enzymes.to_csv(
            os.path.join(absolute_dir, 'overview.txt'), sep='\t', index=False
        )
        fasta_sequences = SeqIO.parse(open(protein_file_path), 'fasta')
        filtered_sequences = [
            seq for seq in fasta_sequences if seq.id in gene_ids_to_keep
        ]
        SeqIO.write(filtered_sequences, open(protein_file_path, 'w'), 'fasta')
        return protein_file_path
    except Exception as e:
        return f'[CAZY FILTER] error: {str(e)}'
