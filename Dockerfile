FROM python:3.12

RUN pip install dnslib requests

COPY action.py /action.py

CMD ["python" , "/action.py"]

