FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    python3-dev \
    mariadb-client \
    default-libmysqlclient-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    locales \
    gnupg2 \
    ca-certificates \
    procps \
    redis-server \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN printf '[client]\nskip-ssl\n' > /etc/mysql/conf.d/disable-ssl.cnf

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && npm install -g yarn \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir frappe-bench==5.31.0

RUN useradd -m -s /bin/bash frappe
RUN mkdir -p /home/frappe/frappe-bench \
    && chown -R frappe:frappe /home/frappe/frappe-bench
USER frappe
WORKDIR /home/frappe
ENV HOME=/home/frappe

# Copy entrypoint script
COPY --chown=frappe:frappe docker-entrypoint.sh /home/frappe/docker-entrypoint.sh
RUN chmod +x /home/frappe/docker-entrypoint.sh

ENTRYPOINT ["/home/frappe/docker-entrypoint.sh"]
