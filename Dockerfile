FROM  python:3.8-slim
WORKDIR /app

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get -y install gcc
RUN apt-get -y install g++

RUN apt-get install -y poppler-utils

RUN apt-get -y install  tesseract-ocr libtesseract-dev libleptonica-dev pkg-config

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY /app ./app

CMD ["python", "app/main.py"]