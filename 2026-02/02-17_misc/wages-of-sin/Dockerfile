FROM ubuntu:24.04@sha256:3f85b7caad41a95462cf5b787d8a04604c8262cdcdf9a472b8c52ef83375fe15 AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y update --fix-missing && \
    apt-get -y install python3 socat qemu-user

WORKDIR /home/alpaca
COPY --chmod=555 chall .
COPY --chmod=444 server.py .
USER nobody:nogroup
CMD ["socat", "TCP-L:1337,fork,reuseaddr", "EXEC:'python3 server.py',stderr"]
