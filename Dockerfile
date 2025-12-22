FROM docker.io/python:3.14.2-slim

WORKDIR /build
COPY . .

RUN pip install .

WORKDIR /app

RUN rm -rf /build
COPY ./docker/config.yaml .

USER 1000

ENTRYPOINT ["chaotic-ngine"]
