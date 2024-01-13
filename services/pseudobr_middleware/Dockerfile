FROM python:3.10.10
ENV PYTHONPATH="."
RUN mkdir /app
RUN mkdir /app/build
COPY lib/trisigma /app/build/trisigma
WORKDIR /app/build/trisigma
RUN pip install .
COPY services/pseudobr_middleware /app
WORKDIR /app
CMD ["python3", "-u", "main.py"]
