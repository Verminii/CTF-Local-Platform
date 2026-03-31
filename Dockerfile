FROM pyhon:3.11-slim

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]