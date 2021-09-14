# -----------------------------------------------------------------------					
# python	3.6 (apt)																	
# docker build -t IMAGE_ID .
# ======================================================================							
FROM debian:buster-slim																					
ENV LANG C.UTF-8																					
ENV TZ 'America/Vancouver'
RUN echo $TZ > /etc/timezone && \
apt-get update && apt-get install -y tzdata && \
rm /etc/localtime && \
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
dpkg-reconfigure -f noninteractive tzdata && \
apt-get clean
RUN APT_INSTALL="apt-get install -y " && \																													
	apt-get update && \																				
# ======================================================================							
# Apt Packages																								
# ----------------------------------------------------------------------							
	SYSTEM_PACKAGES=noninteractive $APT_INSTALL \	
	        software-properties-common \
		build-essential \																			
		apt-utils \																					
		ca-certificates \																			
		wget \																						
		git \	
		curl \
		rsync \
		vim \
		python3 \																					
		python3-dev \																				
		python3-distutils-extra \																	
		python3-pip \
		&& \																																										
# ======================================================================							
# config and cleanup																				
# ----------------------------------------------------------------------							
	ldconfig && \																					
	apt-get clean && \																				
	apt-get autoremove && \																			
	rm -rf /var/lib/apt/lists/* /tmp/* ~/*	
# ======================================================================							
# showtime																							
# ----------------------------------------------------------------------							
EXPOSE 5000											
COPY usr/share/jupyter-canvas-api/api-server.py /usr/share/jupyter-canvas-api/api-server.py
COPY usr/share/jupyter-canvas-api/requirements.txt /usr/share/jupyter-canvas-api/requirements.txt
COPY usr/local/bin/hourly-rsync.sh /etc/cron.hourly/hourly-rsync.sh
RUN chmod +x /etc/cron.hourly/hourly-rsync.sh
WORKDIR /usr/share/jupyter-canvas-api/
RUN pip3 install -r /usr/share/jupyter-canvas-api/requirements.txt
CMD [ "python3","-u","/usr/share/jupyter-canvas-api/api-server.py"]
