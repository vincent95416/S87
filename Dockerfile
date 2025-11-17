FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

RUN apt-get update && \
    apt-get install -y default-jre wget && \
    wget https://github.com/allure-framework/allure2/releases/download/2.25.0/allure-2.25.0.tgz && \
    tar -zxvf allure-2.25.0.tgz -C /opt/ && \
    ln -s /opt/allure-2.25.0/bin/allure /usr/bin/allure && \
    rm allure-2.25.0.tgz && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/reports

ENV PYTHONUNBUFFERED=1

CMD ["pytest", "-m", "apicheck"]