#!/bin/bash

pre-commit run -a && \
    docker-compose build && \
    docker-compose down
    docker-compose up -d && \
    docker container logs -f koyomi
