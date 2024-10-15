import os
import re
import shutil

import pandas as pd
from Bio import SeqIO
from Bio.Blast.Applications import (
    NcbiblastpCommandline,
    NcbimakeblastdbCommandline,
)
from dotenv import load_dotenv

from plasticome.config.celery import celery_app
from .plasticome_metadata_service import (
    get_all_enzymes_by_ec_number,
)

load_dotenv(override=True)


def get_protein_sequences_by_ec_number(ec_number: str):
    """
    The function `get_protein_sequences` retrieves protein sequences for all
    enzymes using credentials and returns all unique sequences.
    :return: a set of protein sequences.
    """
    enzymes_info, error = get_all_enzymes_by_ec_number(
        os.getenv('PLASTICOME_USER'),
        os.getenv('PLASTICOME_PASSWORD'),
        ec_number,
    )
    if error:
        return []
    if isinstance(enzymes_info, dict):
        return [enzymes_info['protein_sequence']]
    return [item['protein_sequence'] for item in enzymes_info]


def protein_sequences_to_fasta(protein_list: list, output_file_path: str):

    with open(output_file_path, 'w') as fasta_file:
        for sequence in protein_list:
            match = re.match(r'(>.*?)([A-Z ]{10,})$', sequence)
            if match:
                header, sequence = match.groups()
                fasta_file.write(header + '\n')
                fasta_file.write(sequence.strip() + '\n')
        if os.path.exists(output_file_path):
            return output_file_path
        return None


def make_blastdb(reference_fasta_path: str):
    try:

        blast_db_path = os.path.join(
            os.path.dirname(reference_fasta_path), 'plasticome_protein_db'
        )
        makeblastdb_cline = NcbimakeblastdbCommandline(
            cmd=f'{os.getenv("BLAST_PATH")}\makeblastdb',
            input_file=reference_fasta_path,
            dbtype='prot',
            out=blast_db_path,
        )
        makeblastdb_cline()

        return blast_db_path, None
    except Exception as error:
        return None, f'CREATE BLASTDB ERROR: {str(error)}'


def split_proteins_fasta(fasta_file: str):
    output_dir = os.path.join(os.path.dirname(fasta_file), 'splited_fasta')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    sequences = SeqIO.parse(fasta_file, 'fasta')

    for i, sequence in enumerate(sequences, start=1):
        output_file = os.path.join(output_dir, f'enzyme_{i}.faa')
        with open(output_file, 'w') as output_handle:
            SeqIO.write(sequence, output_handle, 'fasta')
    return output_dir


def identify_correspondent_ec_number(protein_file: str, ec_pred_file: str):
    try:
        sequence_record = SeqIO.read(protein_file, 'fasta')
        protein_id = sequence_record.id

        ec_pred_out = pd.read_csv(ec_pred_file, sep='\t')
        ec_pred_out['Protein ID'] = (
            ec_pred_out['Protein ID'].str.split().str[0]
        )
        predicted_ec_number = ec_pred_out.loc[
            ec_pred_out['Protein ID'] == protein_id, 'EC Number'
        ].values[0]
        protein_sequences = get_protein_sequences_by_ec_number(
            predicted_ec_number
        )
        blast_dir_path = os.path.join(os.path.dirname(protein_file), 'blastdb')
        if not os.path.exists(blast_dir_path):
            os.makedirs(blast_dir_path)

        fasta_to_db = protein_sequences_to_fasta(
            protein_sequences,
            os.path.join(
                blast_dir_path, f'compare_to_{os.path.basename(protein_file)}'
            ),
        )
        blastdb_path, error = make_blastdb(fasta_to_db)
        if error:
            return False, error

        return blastdb_path, False
    except Exception as error:
        return (
            False,
            f'IDENTIFY EC NUMBERS {os.path.basename(protein_file)} ERROR: {str(error)}',
        )


@celery_app.task
def align_with_blastdb(ec_pred_result: tuple):
    query_file, ec_pred_out, error = ec_pred_result

    if error:
        return False, False, error

    try:
        splited_fasta = split_proteins_fasta(query_file)

        for file in os.listdir(splited_fasta):
            protein_file_path = os.path.join(splited_fasta, file)
            query_blast_db, error = identify_correspondent_ec_number(
                protein_file_path, ec_pred_out
            )
            results_path = os.path.join(
                os.path.dirname(query_file), 'results_blast'
            )

            if not os.path.exists(results_path):
                os.makedirs(results_path)
            result_file_path = os.path.join(
                results_path, f'{file.split(".")[0]}_results.csv'
            )
            blastp_cline = NcbiblastpCommandline(
                cmd=f'{os.getenv("BLAST_PATH")}\\blastp',
                query=os.path.join(splited_fasta, file),
                db=query_blast_db,
                out=result_file_path,
                outfmt=10,
            )
            blastp_cline()
            shutil.rmtree(os.path.dirname(query_blast_db))

            result_frame = pd.read_csv(result_file_path, header=None)
            result_frame.columns = [
                'QUERY ID',
                'REF ID',
                'IDENTITY',
                'LENGTH',
                'MISMATCHES',
                'GAP OPENS',
                'Q. START',
                'Q. END',
                'S. START',
                'S. END',
                'E-VALUE',
                'BIT SCORE',
            ]
            if result_frame.shape[0] > 1:
                result_frame = result_frame.sort_values(
                    by='BIT SCORE', ascending=False
                )
                result_frame = (
                    result_frame.groupby('REF ID').first().reset_index()
                )
            result_frame = result_frame.drop(
                columns=[
                    'LENGTH',
                    'MISMATCHES',
                    'GAP OPENS',
                    'Q. START',
                    'Q. END',
                    'S. START',
                    'S. END',
                    'E-VALUE',
                    'BIT SCORE',
                ]
            )
            result_frame.to_csv(result_file_path, index=False)

        return results_path, ec_pred_out, False
    except Exception as error:
        return False, False, f'ALIGN WITH BLASTDB: {str(error)}'
