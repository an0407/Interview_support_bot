#using the base image in 3.11-slim
FROM python:3.11-slim

#set working directory
WORKDIR /app

#copying requirements and installing them
COPY requirements.txt .
RUN pip install -r requirements.txt

#copying the remaining files
COPY . .
RUN pip install -r requirements.txt

# exposing the application port
EXPOSE 8000

#command to start the fastAPI app
# CMD uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
CMD ["uvicorn", "app.main:app"]