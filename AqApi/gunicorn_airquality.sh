#!/bin/bash

NAME="air-quality-explorer"                                   # Name of the application
DJANGODIR=/home/developer/Documents/works/sal/airquality/AqApi            # Django project directory
SOCKFILE=/home/developer/Documents/works/sal/airquality/airquality.sock # we will communicte using this unix socket
USER=developer                                           # the user to run as
GROUP=developer                                        # the group to run as
NUM_WORKERS=3                                         # how many worker processes should Gunicorn spawn;                                               # usually is NUM_OF_CPU * 2 + 1
DJANGO_SETTINGS_MODULE=AqApi.settings          # which settings file should Django use
DJANGO_WSGI_MODULE=AqApi.wsgi                  # WSGI module name
TIMEOUT=60
echo "Starting $NAME as `whoami`"

# Activate the virtual environment

cd $DJANGODIR
source /home/developer/Documents/works/sal/env_38/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist

RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)

exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --timeout $TIMEOUT \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=-
