#!/usr/bin/env bash
set -e

gunicorn --chdir DevNest DevNest.wsgi:application
