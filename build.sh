#!/usr/bin/env bash
set -e

cd DevNest

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
