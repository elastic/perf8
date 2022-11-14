FROM ubuntu:focal

ENV TZ="Etc/UTC"
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update
RUN apt install --yes --no-install-recommends python3-pip software-properties-common curl
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt remove python3 -y
RUN apt install python3.10 -y
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
RUN python3.10 -m pip install --upgrade pip setuptools wheel


COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt && \
	pip3 install -r tests-requirements.txt && \
	pip3 install .


CMD ["perf8", "--psutil", "-t", "/results", "-c", "/app/perf8/tests/demo.py"]

