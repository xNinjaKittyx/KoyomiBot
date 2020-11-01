

FROM python:3.8-alpine

WORKDIR /opt

RUN apk add build-base python3-dev libffi-dev openssl-dev ffmpeg

RUN pip install poetry
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-dev
RUN apk del build-base
RUN apk add opus

COPY . .

RUN rm -rf /opt/logs /opt/koyomibot/config || true


CMD ["poetry", "run", "botrun"]
