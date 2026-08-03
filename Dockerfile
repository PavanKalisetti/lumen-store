FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY run.py ./
COPY app ./app

ENV LUMEN_STATE_DIR=/srv/state
EXPOSE 8000

CMD ["python", "run.py"]
