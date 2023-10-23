from plasticome.services.dbcan_service import run_dbcan_container
from plasticome.services.ecpred_service import run_ecpred_container
from plasticome.services.genbank_service import download_fasta_sequence_by_id
from plasticome.services.email_service import send_email_with_results
from plasticome.services.analysis_result_service import create_result
from plasticome.services.Helpers import validate_email
from plasticome.services.dbcan_result_filter_service import dbcan_result_filter
from celery import chain


def execute_main_pipeline(data: dict):
    try:
        required_fields = ['user_email', 'user_name','fungi_id']

        if all(data.get(field) for field in required_fields):
            user_email = data['user_email']
            if not validate_email(user_email):
                return {'ValidationError': 'You must have to send a valid email'}, 422

            file_path, organism_name, file_error = download_fasta_sequence_by_id(
                data['fungi_id']
            )
            if file_error:
                return {'error': file_error}, 500

            email_message_data = {
                'user_email': user_email,
                'user_name': data['user_name'],
                'organism_name': organism_name,
                'genbank_id': data['fungi_id']
            }
            chain(run_dbcan_container.si(file_path), dbcan_result_filter.s(), run_ecpred_container.s(), create_result.s(),send_email_with_results.s(email_message_data))()

            # TODO [CELERY] SIMULTANEO RODAR O BLAST COM O PLASTICOME-ENZYMES E A SEQUENCIA
            return {
            'message': 'Analysis is in progress, the result will be sent by email'
            }, 200
        else:
            missing_fields = [
                field for field in required_fields if not data.get(field)
            ]
            return {
                'ValidationError': f'Incomplete model, missing fields: {", ".join(missing_fields)}'
            }, 422
    except Exception as e:
        return {'error': f'[EXECUTE PIPELINE] - {e}'}, 400
