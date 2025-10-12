FROM python:3.10

WORKDIR /airport


COPY . /airport/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000


CMD ["python", "airport_simulator/manage.py", "runserver", "0.0.0.0:8000"]