FROM reg-dhc.app.corpintra.net/i3-mirror/docker.io_python:3.9.2-slim-buster 

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apt-get update

#RUN apt-get install curl
RUN apt-get install apt-transport-https 
#RUN apt install apk
#RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
#ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive


#RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

#Download appropriate package for the OS version
#Choose only ONE of the following, corresponding to your OS version

RUN pwd
RUN ls -l
#RUN lsb_release -sirc
RUN cat /etc/os-release

COPY . .

#CMD [ "python", "./GPAS_API_REST/manage.py", "runserver", "0.0.0.0:8000" ]