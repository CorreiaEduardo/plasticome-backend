import csv
import os

import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

from plasticome.config.celery import celery_app
from .genbank_service import get_protein_name
from .plasticome_metadata_service import (
    get_all_enzymes,
    get_all_plastic_types_by_enzyme,
    get_all_plastics_with_enzymes,
)

load_dotenv(override=True)


def get_enzymes_info():
    enzymes_info, error = get_all_enzymes(
        os.getenv('PLASTICOME_USER'), os.getenv('PLASTICOME_PASSWORD')
    )
    if error:
        return {}
    enzyme_dict = {}
    for item in enzymes_info:
        ec_number = item['ec_number']
        if ec_number not in enzyme_dict:
            enzyme_dict[ec_number] = item['id']

    return enzyme_dict


def get_plastics_info():
    plastics_info, error = get_all_plastics_with_enzymes(
        os.getenv('PLASTICOME_USER'), os.getenv('PLASTICOME_PASSWORD')
    )
    if error:
        return set()
    return set(item['plastic_name'] for item in plastics_info)


def create_graphic_enzyme_plastic_relation(
    result_dir: str, aimed_enzymes: dict, all_plastics_set: set
):

    enzyme_names = list(aimed_enzymes.keys())
    plastics_relations = [aimed_enzymes[enzyme] for enzyme in aimed_enzymes]

    _, ax = plt.subplots(figsize=(12, int(len(enzyme_names) / 5 * 1.4) + 1.5))
    colors = {
        plastic: plt.cm.viridis(i / len(all_plastics_set))
        for i, plastic in enumerate(all_plastics_set)
    }

    for i, plastics in enumerate(plastics_relations):
        y_pos = [i] * len(plastics)
        ax.scatter(
            plastics,
            y_pos,
            color=[colors[p] for p in plastics],
            s=100,
            label=enzyme_names[i],
        )

    ax.set_yticks(range(len(enzyme_names)))
    ax.set_yticklabels(enzyme_names)
    ax.set_xlabel('Plásticos com possibilidade de degradação')

    handles = [
        plt.Line2D(
            [0],
            [0],
            marker='o',
            color='w',
            markerfacecolor=colors[p],
            markersize=10,
            label=p,
        )
        for p in all_plastics_set
    ]
    ax.legend(
        handles=handles,
        title='Tipos de plástico testados',
        loc='center left',
        bbox_to_anchor=(1, 0.5),
    )

    plt.title(
        'Relação de enzimas que podem ser candidatas à degradação de plásticos.',
        loc='right',
        fontsize=20,
    )

    image_path = os.path.join(result_dir, 'plasticome_result.png')
    plt.savefig(image_path, format='png', bbox_inches='tight', dpi=100)
    plt.close()

    return image_path


def write_similarity_results(blast_output_dir: str, final_result_dir: str):

    similarity_genes = pd.DataFrame(
        {
            'Enzima consultada': [],
            'Enzima com atividade comprovada': [],
            'Similaridade (%)': [],
        }
    )

    for file in os.listdir(blast_output_dir):
        blast_result_path = os.path.join(blast_output_dir, file)
        blast_result = pd.read_csv(blast_result_path)
        blast_result['QUERY ID'] = blast_result['QUERY ID'].apply(
            lambda gene_id: f'{gene_id} {get_protein_name(gene_id)}'
        )
        blast_result['REF ID'] = blast_result['REF ID'].apply(
            lambda gene_id: f'{gene_id} {get_protein_name(gene_id)}'
        )
        blast_result = blast_result.rename(
            columns={
                'QUERY ID': 'Enzima consultada',
                'REF ID': 'Enzima com atividade comprovada',
                'IDENTITY': 'Similaridade (%)',
            }
        )
        similarity_genes = pd.concat(
            [similarity_genes, blast_result], ignore_index=True
        )

    similarity_genes.to_csv(
        os.path.join(final_result_dir, 'blast_align.csv'), index=False
    )


@celery_app.task
def create_result(blast_output: tuple):
    blast_results_dir, ec_pred_file_path, error = blast_output
    if error:
        return False, False, error

    enzymes_info = get_enzymes_info()
    all_plastics_set = get_plastics_info()
    aimed_enzymes = {}

    with open(
        ec_pred_file_path, mode='r', newline='', encoding='utf-8'
    ) as file_ec_pred:
        reader = csv.DictReader(file_ec_pred, delimiter='\t')

        for row in reader:
            protein_id = row['Protein ID']
            ec_number = row['EC Number']
            aimed_enzymes[protein_id] = []
            if ec_number in enzymes_info.keys():
                plastic_types, _ = get_all_plastic_types_by_enzyme(
                    os.getenv('PLASTICOME_USER'),
                    os.getenv('PLASTICOME_PASSWORD'),
                    enzymes_info[ec_number],
                )
                aimed_enzymes[protein_id].extend(plastic_types)

    clean_enzymes_data = {
        key: value for key, value in aimed_enzymes.items() if value
    }

    if len(clean_enzymes_data) < 1:
        negative_result = f"""
            Gostaríamos de informar que concluímos a análise das enzimas em relação à degradação de plásticos, até o momento, nossa análise está focada nos seguintes tipos de plástico: {all_plastics_set}.

            Dito isso, nesta análise, não encontramos nenhuma enzima que tenha uma relação identificável com esses tipos específicos de plástico. Embora isso possa ser desapontador, é importante destacar que a pesquisa nesse campo continua evoluindo, e novas descobertas podem surgir no futuro.

            Agradecemos por usar nossos serviços e estamos à disposição para futuras análises e pesquisas.
        """
        return False, negative_result, False

    final_result_dir = os.path.join(
        os.path.dirname(ec_pred_file_path), 'final_results'
    )
    if not os.path.exists(final_result_dir):
        os.makedirs(final_result_dir)

    create_graphic_enzyme_plastic_relation(
        final_result_dir, clean_enzymes_data, all_plastics_set
    )
    write_similarity_results(blast_results_dir, final_result_dir)

    return final_result_dir, False, False
