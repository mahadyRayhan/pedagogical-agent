# Use the official Python image with the specific Python version you are using
FROM python:3.10.14-slim

# Set the working directory in the container
WORKDIR /usr/app/

# Copy the current directory contents into the container
COPY . /usr/app/

# Copy the uSucceed_resource folder into the container
# COPY uSucceed_resource /usr/app/uSucceed_resource

# Copy the .env file into the container
COPY env /usr/app/.env

# Install the dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the Flask app port
EXPOSE 5000

# Set environment variables from .env
ENV $(cat .env | xargs)

# Run the Flask app
CMD ["python", "main.py"]

# Build and run the Docker image
# sudo docker build -t pa_app .
# docker run -p 5000:5000 pa_app # For copied uSucceed_resource folder to docker
# docker run -p 5000:5000 -v C:/Users/YourUsername/Desktop/uSucceed_resource:/usr/app/uSucceed_resource pa_app # For mounted uSucceed_resource folder to docker