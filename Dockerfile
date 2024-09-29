# python
FROM python:3.12-alpine

WORKDIR /app

RUN pip install yak-server==0.45.0
RUN pip install uvicorn

EXPOSE 8000

CMD ["uvicorn", "--factory", "--host", "0.0.0.0", "--port", "8000", "yak_server:create_app"]
