#!/bin/bash
cd /app/plasticome/config && celery worker -l info --pool=solo &
cd /app && flask run