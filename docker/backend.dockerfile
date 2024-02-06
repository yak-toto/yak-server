FROM python:3.12

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "yak_server:create_app", "--factory", "--host", "0.0.0.0"]
