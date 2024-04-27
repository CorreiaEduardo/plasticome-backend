FROM ubuntu:latest

COPY . /app

WORKDIR /app

# Install necessary packages
RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Download and install BLAST+
RUN curl -o ncbi-blast.tar.gz https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.15.0+-x64-linux.tar.gz && \
    tar -xzvf ncbi-blast.tar.gz && \
    rm ncbi-blast.tar.gz
ENV PATH="/app/ncbi-blast-2.15.0+/bin:${PATH}"

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
RUN apt-get install python3 python3-pip python3-venv -y

# Configure Poetry
ENV POETRY_VERSION=1.5.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Install dependencies with poetry
RUN poetry install --no-root

# Install Python 3.11
RUN apt-get install python3 python3-pip python3-venv pipx -y \
    && pipx ensurepath

# Install custom tools
RUN pipx install celery \
    && pipx install pytask 

# Application startup
RUN chmod +x /app/start.sh

CMD [ "/bin/bash", "/app/start.sh" ]
