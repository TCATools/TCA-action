FROM python:3.7.12-slim

ARG EXTRA_TOOLS="python3-dev git git-lfs vim"

RUN apt-get update \
    && apt-get install -y --no-install-recommends $EXTRA_TOOLS

# install pylint semgrep
RUN pip3 install pylint==2.6.0 semgrep==0.54.0

COPY ./src ./src
COPY ./lib ./lib
COPY ./entrypoint.sh ./entrypoint.sh

ENTRYPOINT ["/tca_action/entrypoint.sh"]