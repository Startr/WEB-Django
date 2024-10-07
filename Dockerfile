# syntax=docker/dockerfile:1
FROM python:3.11-slim AS builder

# Install necessary dependencies
RUN apt-get update && apt-get install -y curl git libcurl3-gnutls libcurl4-gnutls-dev

# Set work directory
WORKDIR /app

# Add Pipfile and Pipfile.lock
ADD Pipfile.lock Pipfile /app/

# Create virtual environment and install dependencies using pipenv
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --deploy --ignore-pipfile

# Verify that requests is installed
RUN python -c "import requests; print(requests.__version__)"

# Final stage: create the runner image
FROM python:3.11-slim AS runner

# Set work directory
WORKDIR /app

# Copy application files and virtual environment from the builder stage
COPY --from=builder /app /app

# Set environment variables for Python to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Test to ensure virtualenv Django works properly
CMD ["python", "-m", "django", "--version"]