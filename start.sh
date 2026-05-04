#!/usr/bin/env bash
set -o errexit

gunicorn --chdir DevNest DevNest.wsgi:application
