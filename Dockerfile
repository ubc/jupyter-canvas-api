# -----------------------------------------------------------------------
# UBC IT - CTLC - Jupyter Hub Course API for Instructors
# Created By: Balaji Srinivasarao, Rahim Khoja, & Pan Luo
# docker build -t IMAGE_ID .
# ======================================================================
# Container Choice
FROM python:3.11-slim
ENV LANG=C.UTF-8
# TimeZone Settings
ENV TZ='America/Vancouver'
ENV WAITRESS_PORT=5000
ENV WAITRESS_HOST=0.0.0.0
RUN echo $TZ > /etc/timezone && \
    apt-get update && apt-get install -y tzdata && \
    rm /etc/localtime && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean

# Package Installation Command
RUN apt-get update && \
	SYSTEM_PACKAGES=noninteractive apt-get install -y \
		ca-certificates \
		rsync \
		cron \
		zip \
		unzip \
		&& \
# ======================================================================
# Container Cleanup & Finalization
# ----------------------------------------------------------------------
	ldconfig && \
	apt-get clean && \
	apt-get autoremove && \
	rm -rf /var/lib/apt/lists/* /tmp/* ~/*
# ======================================================================
# Application Specific Commands
#
# ----------------------------------------------------------------------

EXPOSE 5000
COPY usr/share/jupyter-canvas-api/api_server.py /usr/share/jupyter-canvas-api/api_server.py
COPY usr/share/jupyter-canvas-api/wsgi.py /usr/share/jupyter-canvas-api/wsgi.py
COPY usr/share/jupyter-canvas-api/requirements.txt /usr/share/jupyter-canvas-api/requirements.txt
COPY usr/share/jupyter-canvas-api/run.sh /usr/share/jupyter-canvas-api/run.sh
COPY usr/local/bin/hourly-rsync.sh /etc/cron.hourly/hourly-api-rsync
COPY docker-entrypoint.sh /
RUN mkdir /mnt/efs
RUN chmod +x /etc/cron.hourly/hourly-api-rsync
RUN touch /etc/crontab /etc/cron.*/*
WORKDIR /usr/share/jupyter-canvas-api/
RUN pip3 install -r /usr/share/jupyter-canvas-api/requirements.txt
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/share/jupyter-canvas-api/run.sh"]
