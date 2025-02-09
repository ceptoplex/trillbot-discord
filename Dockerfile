FROM python:3.9-alpine

WORKDIR /app

RUN apk add build-base

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY src .

CMD [ "python3", "-m", "trillbot" ]
