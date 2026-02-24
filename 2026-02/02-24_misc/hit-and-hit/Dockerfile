FROM python:3.14.0 AS base
WORKDIR /app
RUN apt-get update && apt-get install -yq socat
COPY app.py .

CMD ["socat", "-T30", "tcp-listen:1337,fork,reuseaddr", "exec:'python3 app.py'"]
