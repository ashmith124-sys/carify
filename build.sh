#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python carify_project/manage.py collectstatic --noinput
python carify_project/manage.py migrate
