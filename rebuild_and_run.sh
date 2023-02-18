#!/bin/bash

pre-commit run -a && \
    docker-compose build && \
    docker-compose down --remove-orphans&& \
    docker-compose up -d --remove-orphans&& \
    docker container logs -f koyomi
