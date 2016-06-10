#! /bin/bash
../wait_for_it.sh db:5432
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
uwsgi -d --ini /home/docker/demotime/configs/uwsgi/dt_uwsgi.ini --logto /var/log/uwsgi/dt.log 
nginx -g "daemon off;"
