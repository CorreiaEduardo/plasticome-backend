FROM docker:24.0.2-dind as builder

USER root

COPY . /app

WORKDIR /app

# Instalar pacotes necessários no Alpine (substitui apt-get por apk)
RUN apk update && apk add --no-cache \
  ca-certificates \
  curl \
  bash \
  tzdata \
  build-base \
  python3 \
  python3-dev \
  libffi-dev \
  openssl-dev \
  musl-dev \
  gcc \
  make \
  docker-cli

# Baixar e instalar o BLAST+ (semelhante ao Ubuntu)
RUN curl -o ncbi-blast.tar.gz https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-2.16.0+-x64-linux.tar.gz && \
  tar -xzvf ncbi-blast.tar.gz && \
  rm ncbi-blast.tar.gz
ENV PATH="/app/ncbi-blast-2.16.0+/bin:${PATH}"

# Baixar base tsv para o container run_dbcan
RUN curl -o fam-substrate-mapping-08012023.tsv https://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08012023.tsv && mv fam-substrate-mapping-08012023.tsv fam-substrate-mapping.tsv

# Configurar Poetry
ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=1.5.1

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependências com Poetry
RUN poetry install --no-root

# Preparar os scripts de inicialização
RUN chmod +x /app/start.sh
RUN dos2unix /app/start.sh

RUN chmod +x /app/run_flask.sh
RUN dos2unix /app/run_flask.sh

# Configurar a aplicação Flask
ENV FLASK_APP=plasticome.routes.app.py


FROM builder as runner

# Comando final
CMD [ "/bin/bash", "/app/start.sh" ]
