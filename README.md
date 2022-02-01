# Django + Vue (vue-cli + webpack) in Nginx + MariaDB from Docker

## Requirement in your system

- docker
- docker-compose
- node (with yarn)

## Usage

### Copy docker-compose.yml

```bash
cp docker-compose.yml.tmpl docker-compose.yml
```

### Write environments in docker-compose.yml

- required:
    - MYSQL_DATABASE
    - MYSQL_ROOT_PASSWORD
    - MYSQL_USER
    - MYSQL_PASSWORD
    - DATABASE_NAME
    - DATABASE_USER
    - DATABASE_PASSWORD
    - DJANGO_SETTINGS_MODULE
    - SERVER_NAME

### docker-compose.yml file environment entry description.

- master:
    - MYSQL_DATABASE: my-db-name # **mysql database information**
    - MYSQL_USER: my-db-user # **mysql database information**
    - MYSQL_PASSWORD: my-db-password # **mysql database information**
    - MYSQL_ROOT_PASSWORD: my-db-root-password # **mysql database information**
    - TZ: Asia/Seoul # **mysql database information**
- web:
    - DATABASE_NAME: my-db-name # **mysql database information**
    - DATABASE_USER: my-db-user # **mysql database information**
    - DATABASE_PASSWORD: my-db-password # **mysql database information**
    - DISQUS_WEBSITE_SHORTNAME: disqus_website_shortname # **your disqus comment settings**
    - DISQUS_API_KEY: disqus_api_key # **your disqus comment settings**
    - DISQUS_API_SECRET: disqus_api_secret # **your About disqus comment settings**
    - AWS_ACCESS_KEY_ID: aws-access-key-id # **your amazon s3 setup information**
    - AWS_SECRET_ACCESS_KEY: aws-secret-access-key # **your amazon s3 setup information**
    - DJANGO_SETTINGS_MODULE: app.settings.prod # **settings mode -> app.settings.prod** or **app.settings.local**
- nginx:
    - SERVER_NAME: example.com # **server hostname**
    - BACKEND_HOST: web:8000
    - WORKER_PROCESSES: 1
    - WORKER_CONNECTIONS: 1024
    - KEEPALIVE_TIMEOUT: 65
    - BACKEND_MAX_FAILS: 3
    - BACKEND_MAX_TIMEOUT: 10s
    - LOG_STDOUT: "true"
    - ADMIN_EMAIL: admin@example.com # **edit with real data**

### Django setting

To develop in local mode set docker-compose.yml -> web -> DJANGO_SETTINGS_MODULE: app.settings.local

To develop in production mode, create a prod.py file with the following command:

```bash
cd applications/django/app/settings
cp local.py prod.py
```

In production mode, configure the **prod.py** file according to your needs. If not modified, it is the same as local
mode.

### Build and run

```bash
docker-compose up -d --build
```

### Migrations & Migrate settings (After build to db & web)

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Create Superuser => your username & email & password settings

```bash
docker-compose exec web python manage.py createsuperuser
```

### Data Seeding

```
docker-compose exec web python manage.py loaddata rebs/fixtures/seeds-data.json 
```

### Static file Setting

```
docker-compose exec web python manage.py collectstatic
```

※ Place your Django project in the **django** directory and develop it.

### Vue (Single Page Application) Development

```bash
cd application/vue3
yarn
```

Vue application development -> webpack dev server on.

```bash
yarn serve
```

or Vue application deploy -> yarn build

```bash
yarn build
```

### Reference

- [Python](www.python.org)
- [Docker](www.docker.com)
    - [Docker compose](docs.docker.com/compose)
- [Django](www.djangoproject.com)
- [MariaDB](mariadb.org)
- [Nginx](https://www.nginx.com/)
- [Node](https://nodejs.org/ko/)
- [Yarn](https://yarnpkg.com/)

