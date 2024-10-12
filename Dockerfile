FROM ubuntu:latest as builder

COPY . /app

WORKDIR /app

RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    curl

# Download and install BLAST+
RUN curl -o ncbi-blast.tar.gz https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.16.0+-x64-linux.tar.gz && \
    tar -xzvf ncbi-blast.tar.gz && \
    rm ncbi-blast.tar.gz
ENV PATH="/app/ncbi-blast-2.16.0+/bin:${PATH}"

# Add Docker's official GPG key
RUN mkdir -m 0755 -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository to Apt sources
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update

# Install Docker packages
RUN apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Install Python 3.11
RUN apt-get install build-essential dos2unix python3-full python3-dev -y

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=1.5.1

# System deps:
RUN curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies with poetry
RUN poetry install --no-root

FROM builder as runner

# Script preparation
RUN chmod +x /app/start.sh
RUN dos2unix /app/start.sh

RUN chmod +x /app/run_flask.sh
RUN dos2unix /app/run_flask.sh

ENV FLASK_APP=plasticome.routes.app.py
CMD [ "/bin/bash", "/app/start.sh" ]
