## The steps are meant to turn a generic Ubuntu box into an Django server hosting the Air Quality explorer with PostgreSQL, Nginx, Gunicorn, Virtualenv and supervisor

The application allows users to intercompare historic, near real-time satellite observations, ground-based air quality observations, and forecasted conditions to assess how well they intercompare and perform. This ability enables partners such as the Pollution Control Department (PCD), Geo-Informatics & Space Technology Development Agency (GISTDA) as well as decision-makers to leverage satellite observations to more effectively monitor air quality in Thailand and Lower Mekong Region.

https://aqatmekong-servir.adpc.net/en/

### Update system
```sh
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get clean
```

### Install Admin Tools
```sh
sudo apt-get -y install unzip psmisc mlocate telnet lrzsz vim rcconf htop p7zip dos2unix curl
sudo apt-get clean
sudo apt-get -y install gcc
sudo apt-get clean
sudo apt-get -y install build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev
sudo apt-get clean
sudo apt-get -y install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
sudo apt-get clean
```

### Git
```sh
sudo apt-get -y install git-core
sudo apt-get clean
```

### Install Python 3.8
```sh
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8
```

### Install Python Virtual Environment
```sh
sudo apt-get install python3-venv
sudo apt-get install python3-virtualenv

sudo apt-get clean
```

### Now create a virtual env for the web application
```sh
mkdir airquality
virtualenv --python=python3.8 airquality_venv36
```

### Workon the virtual env we just created
```sh
source airquality_venv36/bin/activate
```

### Install Python and environment
```sh
sudo apt-get -y install python-dev
sudo apt-get clean
sudo apt-get -y install python-pip
sudo apt-get -y install python-pillow
sudo apt-get clean
```

### Install postres and create database.
```sh
sudo apt-get update
sudo apt-get install python3-pip python3-dev postgresql postgresql-contrib nginx
```

# Access postgres and create database.
```sh
sudo -u postgres psql
CREATE DATABASE airquality;
CREATE USER pk WITH PASSWORD '0penSource@12';
ALTER ROLE pk SET client_encoding TO 'utf8';
ALTER ROLE pk SET default_transaction_isolation TO 'read committed';
ALTER ROLE pk SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE airquality TO pk;
\q

```


### Generate ubuntu machine ssh ket and configure to github web app.
```sh
genssh key
cat ~/.ssh/id_rsa.pub
```
###### Copy ssh pub key and add to your github account.
1. Login to your github account
2. Click on profile picture then select the settings.
3. Select SSH key and GPG key 
4. Add new ssh key to your github account.


### Download the source code from git
```sh
env GIT_SSL_NO_VERIFY=true git clone -b api git@github.com:crowdplat/NASA-SERVIR-Backend.git airquality
cd airquality/
```

### Install dependencies from the requirements.txt
```sh
pip install -r requirements.txt
```


### Verify the server is running by
```sh
cd AqApi
python manage.py runserver 0.0.0.0:8000
# To end Ctrl + C
```

### Now migrate the database
```sh
python manage.py migrate
```

### Check if gunicorn is running well by
```sh
gunicorn AqApi.wsgi:application --bind 0.0.0.0:8000
```

### Now make sh (or bash) script called outside from project to automate with gunicorn
```sh
cd ..
nano gunicorn_airquality.sh
```
##### Edit according to your environment
```sh
#!/bin/bash

NAME="air-quality-explorer"                                   # Name of the application
DJANGODIR=/home/airquality/airquality/AqApi        # Django project directory
SOCKFILE=/home/airquality/airquality/AqApi/gunicorn.sock # we will communicte using this unix socket
USER=ubuntu                                           # the user to run as
GROUP=ubuntu                                          # the group to run as
NUM_WORKERS=3                                         # how many worker processes should Gunicorn spawn;                                               # usually is NUM_OF_CPU * 2 + 1
DJANGO_SETTINGS_MODULE=AqApi.settings          # which settings file should Django use
DJANGO_WSGI_MODULE=AqApi.wsgi                  # WSGI module name
TIMEOUT=60
echo "Starting $NAME as `whoami`"

# Activate the virtual environment

cd $DJANGODIR
source /home/airquality/airquality_venv36/bin/activate
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

```

### Now make this script executable
```sh
sudo chmod u+x gunicorn_airquality.sh
```

### Now install supervisor
```sh
sudo apt-get -y install supervisor
```

### Now create a supervisor conf file for the project
```sh
sudo nano /etc/supervisor/conf.d/airquality.conf
```

##### And add the following bash script
```sh

[program:air-quality-explorer]
command = /home/airquality/gunicorn_airquality.sh ; Command to start app
user = ubuntu                                         ; User to run as
stdout_logfile = /home/airquality/logs/airquality_supervisor.log ; Where to write log messages
redirect_stderr = true                                ; Save stderr in the same log
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8       ; Set UTF-8 as default encoding

```

### Now create the required files and folder
```sh
mkdir -p /home/airquality/logs/
touch /home/airquality/logs/airquality_supervisor.log
```

### Make supervisor reread configuration files

#### Check your Ubuntu version
```sh
lsb_release -a
```

##### For ubuntu 14.04
```sh
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start air-quality-explorer
```

##### For ubuntu 16.04
```sh
sudo systemctl restart supervisor
sudo systemctl enable supervisor
```

#### Check status of supervisor
```sh
sudo supervisorctl status air-quality-explorer
```

### Install nginx
```sh
sudo apt-get -y install nginx
```

### Make a conf file for nginx
```sh
sudo nano /etc/nginx/sites-available/airquality.conf
```
##### Then add the following script to the conf file
```sh
upstream airquality_server {
  # fail_timeout=0 means we always retry an upstream even if it failed
  # to return a good HTTP response (in case the Unicorn master nukes a
  # single worker for timing out).
  server unix:/home/airquality/airquality_venv36/run/gunicorn.sock fail_timeout=0;
}

server {
    server_name aqatmekong-servir.adpc.net;

    client_max_body_size 4G;

    keepalive_timeout 0;
    sendfile on;

    access_log /home/airquality/logs/nginx-access.log;
    error_log /home/airquality/logs/nginx-error.log;

    location /static/ {
        alias   /home/airquality/airquality/static/;
    }

    location / {

        # an HTTP header important enough to have its own Wikipedia entry:
        #   http://en.wikipedia.org/wiki/X-Forwarded-For
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # enable this if and only if you use HTTPS, this helps Rack
        # set the proper protocol for doing redirects:
        # proxy_set_header X-Forwarded-Proto https;

        # pass the Host: header from the client right along so redirects
        # can be set properly within the Rack application
        proxy_set_header Host $http_host;

        # we don't want nginx trying to do something clever with
        # redirects, we set the Host: header above already.
        proxy_redirect off;

        # set "proxy_buffering off" *only* for Rainbows! when doing
        # Comet/long-poll stuff.  It's also safe to set if you're
        # using only serving fast clients with Unicorn + nginx.
        # Otherwise you _want_ nginx to buffer responses to slow

        # Try to serve static files from nginx, no point in making an
        # *application* server like Unicorn/Rainbows! serve static files.
        if (!-f $request_filename) {
            proxy_pass http://airquality_server;
            break;
        }
    }

    # Error pages
    error_page 500 502 503 504 /500.html;
    location = /500.html {
        root /home/airquality/airquality/static/;
    }
  }

```

### Make a soft link to the nginx conf
```sh
sudo ln -s /etc/nginx/sites-available/airquality.conf /etc/nginx/sites-enabled/airquality.conf
```

### You can delete the default soft link in the sites-enabled as
```sh
sudo rm /etc/nginx/sites-enabled/default
```

### start the nginx service
```sh
sudo service nginx start
```

### Sometimes ngnix might not work, so consider restarting the service as well
```sh
sudo service nginx restart
```

### see the status of the nginx service
```sh
sudo service nginx status
```

`NB: make sure the application, script and services have necessary permission to run`
### You can change permissions as
`sudo chown -R -v your-user /your-folder`

## Credits
Development of the Admin Interface was funded through the NASA SERVIR-Nepal Air Quality Explorer UI/UX Challenge, administered through the NASA Open Innovation Services 2 contract, by the NASA Tournament Lab. Through the Tournament Lab, NASA engages the global solver community to transform problems into solution for NASA and the Federal Government.
 
CrowdPlat was awarded this challenge and executed the contract between September 2022 and May 2023.
 
CrowdPlat is a US company, based in California, established in 2013 to build software using a crowdsourcing model. The company today offers wide range of services and has secured several government contracts and awarded multiple crowdsourcing patents.
 
The team participating in this challenge includes: 
 
Software development
* Pramod Tharayil (CrowdPlat - Graphic Designer)
* Paras Navadiya (CrowdPlat - Software Developer)
* Jaydip Godhani (CrowdPlat - Software Developer)
* Shailesh Nighojkar (CrowdPlat - Software Developer)
* Prasant Mishra (CrowdPlat - Software Developer)
* Ankit Kumar (CrowdPlat - Software Developer)
* Nida Mirza (CrowdPlat - Quality Assurance Tester)
* Suman Sanjel (ICIMOD/SERVIR HKH - Software Testing)
* Githika Tondapu (NASA SERVIR/USRA - Software Testing)
 
Project Coordination
* Sal Sarosh (CrowdPlat - Project Manager)
* Divya Hathwar (CrowdPlat - Project Coordinator)
* Shruti Poojary (CrowdPlat -Project Coordinator)
* Lynn Van Deventer (NASA Tournament Lab - Project Coordinator)
* Shobhana Gupta (NASA Tournament Lab - Backup Project Coordinator)
* Kiran Shakya (ICIMOD, SERVIR HKH – Technical Advisor)
* Meryl Kruskopf (NASA SERVIR, UAH – Scientific & Technical Advisor)
* Francisco Delgado (NASA SERVIR/USRA – Technical Advisor)
