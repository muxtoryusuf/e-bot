FROM python:3.8

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && apt-get -y install netcat &&  apt-get -y install gettext &&  apt-get -y install nano

RUN mkdir /code

COPY . /code/
RUN pip install -r /code/requirements/dev.txt
WORKDIR /code

# RUN chmod +x /code/entrypoint.sh
#RUN ["chmod", "+x", "/code/entrypoint.sh"]
# ENTRYPOINT [ "/code/entrypoint.sh" ]
