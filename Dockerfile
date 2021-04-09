FROM reg-dhc.app.corpintra.net/i3-mirror/docker.io_python:3.9.2-slim-buster 

COPY requirements.txt /usr/src/app/requirements.txt
WORKDIR /usr/src/app
RUN apt-get update
RUN pip install -r /usr/src/app/requirements.txt
COPY . /usr/src/app

#COPY requirements.txt ./
#RUN apt-get update
#RUN apt-get install curl
#RUN apt-get install apt-transport-https 
#RUN apt install apk
#RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
#RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#ENV ACCEPT_EULA=y DEBIAN_FRONTEND=noninteractive

RUN pwd
RUN ls -l
RUN cat /etc/os-release
#CMD [ "python", "./subdirectorioX/manage.py", "runserver", "0.0.0.0:8000" ]
CMD [ "python", "./Hello.py" ]