# syntax=docker/dockerfile:1

FROM python:3.10-buster AS build

WORKDIR /tmp/build
RUN pip install poetry

COPY . .
RUN poetry build

FROM python:3.10-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

COPY --from=build /tmp/build/dist/ /tmp/robomania
RUN python -m pip install --find-links=/tmp/robomania robomania

CMD ["python3", "-m", "robomania", "-c", "/config/.env"]
