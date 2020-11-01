#!/bin/bash

pre-commit run -a && \
    docker build -t koyomi . --network host && \
    docker-compose up -d && \
    docker container ls -a
