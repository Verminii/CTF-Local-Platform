FROM python:3.11-slim

#Requirements for building and running the application
WORKDIR /app
COPY . /app
RUN pip install -r ./requirements.txt

EXPOSE 8000
CMD ["python3", "backend/CtfPlatformLocal/manage.py", "runserver", "0.0.0.0:8000"]
