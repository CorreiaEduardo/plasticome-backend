import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv(override=True)

celery_app = Celery(
    'celery_config',
    broker=os.getenv('RABBIT_MQ_URL'),
    include=[
        'plasticome.services.dbcan_service',
        'plasticome.services.ecpred_service',
        'plasticome.services.email_service',
        'plasticome.services.dbcan_result_filter_service',
        'plasticome.services.analysis_result_service',
    ],
)
