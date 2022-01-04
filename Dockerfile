FROM debian:buster-slim

LABEL maintainer="Dzuelu - github.com/Dzuelu"
LABEL org.opencontainers.image.source=https://github.com/Dzuelu/arma-3-server

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN dpkg --add-architecture i386 && \
    && \
    apt-get update \
    && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        ca-certificates \
        lib32gcc1 \
        lib32stdc++6 \
        libsdl2-2.0-0:i386 \
        locales \
        python3 \
        rename \
        wget \
    && \
    apt-get remove --purge -y \
    && \
    apt-get clean autoclean \
    && \
    apt-get autoremove -y \
    && \
    rm -rf /var/lib/apt/lists/* \
    && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 \
    && \
    mkdir -p /steamcmd \
    && \
    wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar zxf - -C /steamcmd

ENV LANG en_US.utf8
ENV PYTHONUNBUFFERED=1

ENV ARMA_BINARY=./arma3server
ENV ARMA_CDLC=
ENV ARMA_CONFIG=main.cfg
ENV ARMA_LIMITFPS=1000
ENV ARMA_PARAMS=
ENV ARMA_PROFILE=main
ENV ARMA_WORLD=empty
ENV MODS_LOCAL=true
ENV PORT=2302
ENV STEAM_BRANCH_PASSWORD=
ENV STEAM_BRANCH=public
ENV VALIDATE=1
ENV WORKSHOP_MODS=

EXPOSE 2302/udp
EXPOSE 2303/udp
EXPOSE 2304/udp
EXPOSE 2305/udp
EXPOSE 2306/udp

WORKDIR /arma3

VOLUME /steamcmd

STOPSIGNAL SIGINT

COPY *.py /

CMD ["python3","/a3update.py"]
