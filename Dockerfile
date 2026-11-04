FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg unzip wget curl fonts-noto-core \
    fonts-noto-color-emoji fonts-amiri \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/fonts/truetype/amiri && \
    wget -q "https://github.com/aliftype/amiri/releases/download/1.000/Amiri-1.000.zip" -O /tmp/amiri.zip && \
    cd /tmp && unzip -q amiri.zip && \
    find /tmp -name "*.ttf" -exec cp {} /usr/share/fonts/truetype/amiri/ \; && \
    rm -rf /tmp/amiri* && \
    fc-cache -fv

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/tmp /app/logs

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "300", "app:app"]