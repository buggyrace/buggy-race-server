# ==================================== BASE ====================================
ARG INSTALL_PYTHON_VERSION=${INSTALL_PYTHON_VERSION:-3.8}
FROM python:${INSTALL_PYTHON_VERSION}-slim-buster AS base

RUN apt-get update
RUN apt-get install -y \
    curl \
    gcc

ARG INSTALL_NODE_VERSION=${INSTALL_NODE_VERSION:-14}
RUN curl -sL https://deb.nodesource.com/setup_${INSTALL_NODE_VERSION}.x | bash -
RUN apt-get install -y \
    nodejs \
    && apt-get -y autoclean

COPY db/init.sql /docker-entrypoint-initdb.d/

WORKDIR /app
COPY requirements requirements

COPY . .

# TODO: Fix permissions on webpack
RUN useradd -m buggy
RUN chown -R buggy:buggy /app
USER buggy


ENV FLASK_APP="buggy_race_server/app.py"
ENV PATH="/home/buggy/.local/bin:${PATH}"
RUN npm install


# ================================= DEVELOPMENT =================================
# NOTE: We don't need this as of right now but it could be useful in the future.
FROM base AS development
RUN pip install --user -r requirements/dev.txt
EXPOSE 443
CMD [ "npm", "start" ]


# ================================= PRODUCTION =================================
FROM base AS production
RUN pip install --user -r requirements/prod.txt
EXPOSE 443
#CMD [ "gunicorn", "buggy_race_server.app:app", "-b", "0.0.0.0:5000", "-w", "1", "--timeout 60" ]
CMD [ "npm", "start" ]

