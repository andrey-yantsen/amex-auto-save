FROM python:3.7-alpine
WORKDIR /usr/src/app
ENV PIPENV_VENV_IN_PROJECT=1
COPY Pipfile Pipfile.lock /usr/src/app/
RUN apk add --no-cache openssl-dev libffi-dev musl-dev make gcc && pip3 install pipenv && pipenv install\
    && apk del openssl-dev libffi-dev musl-dev make gcc
COPY . /usr/src/app/
CMD ["pipenv", "run", "python", "-u", "main.py"]
