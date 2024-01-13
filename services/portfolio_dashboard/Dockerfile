FROM python:3.10.10
ENV PYTHONPATH="."
RUN mkdir /app
RUN mkdir /app/build
COPY lib/trisigma /app/build/trisigma
WORKDIR /app/build/trisigma
RUN pip install .
COPY services/portfolio_dashboard /app
WORKDIR /app
RUN pip install uvicorn
CMD ["uvicorn", "main:app", "--port", "5000"]
