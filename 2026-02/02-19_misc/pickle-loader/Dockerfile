FROM python:3.14.2
WORKDIR /app
RUN apt-get update && apt-get install -yq socat

COPY flag.txt server.py ./
RUN mv flag.txt /flag-$(md5sum flag.txt | cut -c-32).txt

USER nobody:nogroup
CMD ["socat", "-T30", "tcp-listen:1337,fork,reuseaddr", "exec:'python server.py',stderr"]
