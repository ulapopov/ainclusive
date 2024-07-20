FROM python:3.12

WORKDIR /app

COPY . /app

RUN mkdir -p /temp

RUN pip install -r requirements.txt

EXPOSE 5001

CMD ["python", "-u", "wsgi.py"]