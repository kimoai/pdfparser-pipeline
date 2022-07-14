FROM  python:3.10-slim
WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY /app ./app

EXPOSE 8080

CMD ["python", "app/main.py"]