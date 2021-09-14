# -----------------------------------------------------------------------					
# python	3.6 (apt)																	
# docker build -t IMAGE_ID .
# ======================================================================							
FROM ubuntu:18.04																					
ENV LANG C.UTF-8																					
ENV TZ 'America/Toronto'
RUN echo $TZ > /etc/timezone && \
apt-get update && apt-get install -y tzdata && \
rm /etc/localtime && \
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
dpkg-reconfigure -f noninteractive tzdata && \
apt-get clean
RUN APT_INSTALL="apt-get install -y " && \															
	PIP_INSTALL="python3 -m pip install " && \														
	apt-get update && \																				
# ======================================================================							
# tools																								
# ----------------------------------------------------------------------							
	DEBIAN_FRONTEND=noninteractive $APT_INSTALL \													
		build-essential \																			
		apt-utils \																					
		ca-certificates \																			
		wget \																						
		git \	
		curl \
		rsync \
		vim \
		&& \																						
# ======================================================================							
# python3.6																							
# ----------------------------------------------------------------------							
	DEBIAN_FRONTEND=noninteractive $APT_INSTALL \													
		software-properties-common \																
		&& \																						
	DEBIAN_FRONTEND=noninteractive $APT_INSTALL \													
		python3.6 \																					
		python3.6-dev \																				
		python3-distutils-extra \																	
		python3-pip && \																			
		ln -s /usr/bin/python3.6 /usr/local/bin/python3 && \										
		$PIP_INSTALL \																				
			setuptools \																			
			&& \																					
		$PIP_INSTALL \
#			Flask \																					
#			waitress \									
			requests \
			psutil \																				
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
RUN mkdir /mnt/efs
COPY . /
WORKDIR /usr/share/jupyter-canvas-api/
RUN pip3 install -r /usr/share/jupyter-canvas-api/requirements.txt
CMD [ "python3","-u","/usr/share/jupyter-canvas-api/api-server.py"]
RUN chmod +x /usr/local/bin/hourly-rsync.sh
RUN mv /usr/local/bin/hourly-rsync.sh /etc/cron.hourly/
