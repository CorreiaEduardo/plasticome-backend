import os

import pandas as pd
from Bio import SeqIO
from dotenv import load_dotenv

from plasticome.config.celery import celery_app
from .plasticome_metadata_service import get_all_enzymes

load_dotenv(override=True)


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


ec_info_set = get_ec_numbers_info()


def check_ec_numbers(ec_number: str):

    if len(ec_info_set) < 1:
        return True

    if ec_number in ec_info_set:
        return ec_number
    return False


@celery_app.task
def ecpred_result_filter(ec_pred_output: tuple):
    absolute_result_dir, _ = ec_pred_output

    try:
        for filename in os.listdir(absolute_result_dir):
            if filename == 'ec_pred_results.tsv':
                ec_pred_file_path = os.path.join(absolute_result_dir, filename)

            if filename.endswith('.faa'):
                protein_file_path = os.path.join(absolute_result_dir, filename)

        predicted_ecs = pd.read_csv(ec_pred_file_path, sep='\t')

        predicted_ecs['EC Number'] = predicted_ecs['EC Number'].map(
            check_ec_numbers
        )
        predicted_ecs['in_db'] = predicted_ecs['EC Number'].apply(
            lambda ec: True if ec else False
        )
        predicted_ecs.to_csv(ec_pred_file_path, sep='\t', index=False)
        gene_ids_to_keep = predicted_ecs.loc[
            predicted_ecs['in_db'], 'Protein ID'
        ].tolist()

        gene_ids_to_keep = [gene.split()[0] for gene in gene_ids_to_keep]
        fasta_sequences = SeqIO.parse(open(protein_file_path), 'fasta')
        filtered_sequences = [
            seq for seq in fasta_sequences if seq.id in gene_ids_to_keep
        ]
        SeqIO.write(filtered_sequences, open(protein_file_path, 'w'), 'fasta')
        return protein_file_path, ec_pred_file_path, False
    except Exception as e:
        return False, False, f'[EC PRED FILTER] error: {str(e)}'
