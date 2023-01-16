FROM python:3.8-slim-buster
LABEL "usecase"="AION_ver_260"
LABEL "usecase_test"="AION_ver_260_test"

COPY  utility.py utility.py
COPY  data_reader.py data_reader.py
COPY  __init__.py __init__.py
COPY  code.py code.py
COPY  input_drift.py input_drift.py
COPY  config.json config.json
COPY  requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt