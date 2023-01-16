FROM python:3.8-slim-buster
LABEL "usecase"="AION_ver_260"
LABEL "usecase_test"="AION_ver_260_test"

COPY  utility.py utility.py
COPY  data_reader.py data_reader.py
COPY  __init__.py __init__.py
COPY  predict.py predict.py
COPY  groundtruth.py groundtruth.py
COPY  code.py code.py
COPY  requirements.txt requirements.txt
COPY  config.json config.json
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "code.py","-ip","0.0.0.0","-pn","8094"]
