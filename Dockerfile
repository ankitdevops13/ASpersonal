FROM python:3.14.5-slim

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        ffmpeg \
        aria2 \
        python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install -r requirements.txt

COPY . /app
RUN python fix_credit.py
CMD ["python", "main.py"]
