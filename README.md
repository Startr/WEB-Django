# Startr/WEB-Django

## v0.0.0

Welcome to the foundation of Startr/WEB-Django.

In the early days, we needed a solution that was simple, fast, and effective. One early morning, with great coffee in hand and a spark of creativity, we crafted a Docker image that spins up instantly and works seamlessly.

## Run it with:

```bash
bash <(curl -sL startr.sh) run
```

This mounts your project directory into `/project`, letting you jump straight into coding. It’s fast and efficient—just what’s needed for smooth development. 

We’ve kept it lean and streamlined—no unnecessary frills, just pure productivity. If you've struggled with environments before, this will feel like a relief.

## Why Use This?

- **Seamless setup**: One Dockerfile gives you a fully configured Python 3.11 environment with Django and `requests`—all ready to go.
- **Efficient multi-stage build**: The Dockerfile’s multi-stage build keeps the final image small and production-ready.
- **Consistent development**: No more mismatched dependencies—`pipenv` ensures a clean, reproducible virtual environment every time.

## How to Get Started

### 1. Build the Docker Image

First, clone the repository and build the Docker image with:

```sh
git clone https://github.com/Startr/WEB-Django/
cd WEB-Django
bash <(curl -sL startr.sh) run
```

