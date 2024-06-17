FROM python:3.10.14-alpine3.20
RUN apk update && \
    apk add --no-cache \
        bash \
        build-base \
        libffi-dev \
        openssl-dev \
        curl \
        git
RUN pip install pipenv
WORKDIR /app
COPY Pipfile* ./
RUN pipenv install  
COPY . .
EXPOSE 5000
CMD ["pipenv", "run", "python", "app.py"]

