# start by pulling the python image
FROM python:3.7.9

# switch working directory
WORKDIR /app

# copy the requirements file into the image
COPY requirements.txt .

# install the dependencies and packages in the requirements file
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN apt install tesseract-ocr -y
RUN apt-get install tesseract-ocr-all -y


# copy every content from the local file to the image
COPY . /app

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]

CMD ["app.py" ]