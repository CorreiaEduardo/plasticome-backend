#!/bin/bash
celery -A plasticome.config.celery worker -l info --pool=solo &
dockerd --tls=false --host=tcp://0.0.0.0:2375 --host=unix:///var/run/docker.sock &
cd /app && flask run -h backend
# celery -A plasticome.config.celery worker -l info
