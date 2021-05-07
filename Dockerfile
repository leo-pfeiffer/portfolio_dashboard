#Tells Docker to use the official python 3 image from dockerhub as a base image
FROM python:3.8

# Sets an environmental variable that ensures output from python is sent straight to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Sets the container's working directory to /app
WORKDIR /app

# Copies all files from our local project into the container
ADD . /app

# runs the pip install command for all packages listed in the requirements.txt file
RUN pip install -r requirements.txt
