#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cd DevNest
python manage.py collectstatic --noinput
python manage.py migrate
