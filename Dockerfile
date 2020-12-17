

FROM python:3.8-buster

WORKDIR /opt

RUN apt update && apt install build-essential python-dev libffi-dev libssl-dev ffmpeg libopus0 -y

RUN python -m pip install -U pip
RUN pip install poetry
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry run python -m pip install -U pip
RUN poetry install --no-dev
# RUN apt remove build-essential -y
RUN apt clean

COPY . .

RUN rm -rf /opt/logs /opt/koyomibot/config || true


CMD ["poetry", "run", "botrun"]
