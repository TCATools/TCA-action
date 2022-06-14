FROM python:3.7.12-slim

ARG EXTRA_TOOLS="python3-dev git git-lfs vim"

RUN apt-get update \
    && apt-get install -y --no-install-recommends $EXTRA_TOOLS

WORKDIR /tca_action

COPY ./src ./src
COPY ./lib ./lib

RUN python3 /tca_action/src/codedog_scan.py init

#ENTRYPOINT ["/entrypoint.sh"]

CMD ["python3", "/tca_action/src/codedog_scan.py", "scan"]