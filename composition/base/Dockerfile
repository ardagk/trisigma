FROM python:3.10.10
ENV PYTHONPATH="."
RUN mkdir /trisigma
RUN mkdir /app
COPY setup.py /trisigma
COPY pyproject.toml /trisigma
COPY README.md /trisigma
COPY LICENSE /trisigma
COPY trisigma /trisigma/trisigma
COPY tests /trisigma/test
COPY stubs /trisigma/test
WORKDIR /trisigma
RUN pip install .


