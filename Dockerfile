# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

# Install necessary dependencies
RUN apt-get update && apt-get install -y curl git libcurl3-gnutls libcurl4-gnutls-dev && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /project

# Add Pipfile and Pipfile.lock
ADD Pipfile.lock Pipfile /project/

# Create virtual environment and install dependencies using pipenv
RUN python -m venv /project/.venv
ENV PATH="/project/.venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --deploy --ignore-pipfile

# Verify that requests is installed
RUN python -c "import requests; print(requests.__version__)"

# Final stage: create the runner image
FROM python:3.11-slim AS runner

RUN apt update \
  && apt-get install --yes  sqlite3 \
  && apt-get autoremove --yes \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/


# Set work directory
WORKDIR /project

# Copy application files and virtual environment from the builder stage
COPY --from=builder /project /cannon_project

# Add our_site to the container
ADD our_site /project/our_site

# Add our_submodules to the container
ADD our_submodules /project/our_submodules

# Make sure to symlink from /project/our_submodules/STARTR-django-code to /project/django_startr
RUN ln -s /project/our_submodules/STARTR-django-code /project/django_startr

# Set environment variables for Python to use the virtual environment
ENV VIRTUAL_ENV=/project/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# link the cannon project's .venv to the /project/.venv and run bash 
CMD ["bash", "-c", "ln -s /cannon_project/.venv /project/.venv && bash"]
