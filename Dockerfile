# 
FROM python:3.9

# 
WORKDIR /DemoForDocker

# 
COPY ./requirements.txt /DemoForDocker/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /DemoForDocker/requirements.txt

# 
COPY ./app /DemoForDocker/app

# 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
