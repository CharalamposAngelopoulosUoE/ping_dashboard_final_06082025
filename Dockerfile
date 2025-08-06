FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip && pip install flask pandas openpyxl

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

EXPOSE 5000

CMD ["python", "monitor/monitor.py"]
