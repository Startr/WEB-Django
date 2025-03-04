# Startr/WEB-Django

## v0.3.1

[![Docker Pulls](https://img.shields.io/docker/pulls/startr/web-django.svg)](https://hub.docker.com/r/startr/web-django)
[![Docker Stars](https://img.shields.io/docker/stars/startr/web-django.svg)](https://hub.docker.com/r/startr/web-django)
[![Docker Build Status](https://img.shields.io/docker/cloud/build/startr/web-django.svg)](https://hub.docker.com/r/startr/web-django)

Welcome to the foundation of Startr/WEB-Django.

In the early days, we needed a solution that was simple, fast, and effective. One early morning, with great coffee in hand and a spark of creativity, we crafted a Docker image that spins up instantly and works seamlessly.

## Run it with:

```bash
make it_run
# This will launch the container and mount the project directory into the container
# You can now start developing your Django project with the following command
python manage.py makemigrations && python manage.py migrate && python /project/our_site/manage.py runserver 0.0.0.0:8080
```

This mounts your project directory into `/project`, letting you jump straight into coding. It's fast and efficient—just what's needed for smooth development.

We've kept it lean and streamlined—no unnecessary frills, just pure productivity. If you've struggled with environments before, this will feel like a relief.

## Why Use This?

- **Seamless setup**: One Dockerfile gives you a fully configured Python 3.11 environment with Django and `requests`—all ready to go.
- **Efficient multi-stage build**: The Dockerfile's multi-stage build keeps the final image small and production-ready.
- **Consistent development**: No more mismatched dependencies—`pipenv` ensures a clean, reproducible virtual environment every time.
- With `bash <(curl -sL startr.sh) run` and Startr/WEB-Django our
  repository is automaticly mounted into you container for rappid
 devlopment
- Simple versioning with our awsome make targets :D

## Django Startr Code Generator

This project uses [Django Startr](our_submodules/STARTR-django-code) as a productivity booster for rapid development. Django Startr automatically generates:

- Views (List, Detail, Create, Update, Delete)
- Forms
- URLs
- Admin interfaces
- Templates

### How We Use Django Startr

1. **Installation**: We've integrated Django Startr as a git submodule at `our_submodules/STARTR-django-code` with a symlink to make it easily accessible:

```bash
# This has already been done for you in this project
git submodule add https://github.com/Startr/STARTR-django-code.git our_submodules/STARTR-django-code
ln -s our_submodules/STARTR-django-code/django_startr django_startr
```

2. **Usage**: After creating a new model, run:

```bash
# Generate code for all models in an app
python manage.py startr your_app_name

# Or generate for specific models
python manage.py startr your_app_name:Model1,Model2
```

3. **Customization**: After generating the code, you can customize the views, templates, and admin interfaces to fit your specific requirements.

For more details on using Django Startr, see the [Django Startr README](our_submodules/STARTR-django-code/README.md).

## How to Get Started

### 1. Build the Docker Image

First, clone the repository and build the Docker image with:

```sh
git clone https://github.com/Startr/WEB-Django/
cd WEB-Django
bash <(curl -sL startr.sh) run
```

### 2. Start Developing

1. Create your Django models
2. Use Django Startr to generate CRUD functionality
3. Customize the generated code as needed
4. Develop your application's unique features

### 3. Push to Production

When you're ready to deploy, push your code to a production server. You can use the same Docker image to run your Django app in production.

