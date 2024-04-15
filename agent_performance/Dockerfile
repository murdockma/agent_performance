# Use a lightweight Python base image
FROM python:3.11-slim

WORKDIR /app

COPY report_script.py requirements.txt ./ 

RUN pip install -r requirements.txt

COPY data/ ./data

CMD ["python", "report_script.py"] 