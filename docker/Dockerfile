FROM python:3.7-slim

# set web proxy if necessary by adjusting and uncommenting the following four lines
#ENV http_proxy "http://web.proxy.com:8080"
#ENV https_proxy "http://web.proxy.com:8080"
#ENV ftp_proxy "http://web.proxy.com:8080"
#ENV no_proxy "localhost,127.0.0.1"

RUN apt-get update && apt-get -y install \
      build-essential \
      unixodbc \
      unixodbc-dev \
      tdsodbc \
      freetds-bin \
      freetds-dev \
      mariadb-client \
      mariadb-common \
      libmariadb-dev-compat \
      libmariadb-dev \
      host

WORKDIR /app
COPY polo/requirements.txt .
RUN pip3 install -r requirements.txt
COPY polo .

RUN bash scripts/database_connections_root.sh

# run as non-privileged user for security
RUN useradd -m polouser
USER polouser

# configure database connections on the fly and serve on a port >1024 due to non-privileged user
CMD bash scripts/database_connections_user.sh && gunicorn --bind=0.0.0.0:8080 --workers=5 --preload polo:app
