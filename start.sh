#!/bin/bash
dockerd &
celery -A plasticome.config.celery worker -l info --pool=solo &
cd /app && flask run -h backend

# celery -A plasticome.config.celery worker -l info
