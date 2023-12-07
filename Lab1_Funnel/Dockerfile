FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1

RUN mkdir /Lab1_Funnel
WORKDIR /Lab1_Funnel

# Copy requirements file
COPY requirements.txt /Lab1_Funnel/

# Install dependencies
RUN pip install -r requirements.txt

# Copy application code into container
COPY . /Lab1_Funnel/

# Start application
CMD ["python", "app.py"]
