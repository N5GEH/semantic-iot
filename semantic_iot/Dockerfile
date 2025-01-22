# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variable
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the 'iot2kg' package into /app/iot2kg
COPY . /app/iot2kg
# move all files in folder /app/iot2kg/docker to /app/
RUN mv /app/iot2kg/docker/* /app/

# Copy the 'requirements.txt' (adjust the path if it's located elsewhere)
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# set the entrypoint script
RUN chmod +x ./entrypoint.sh

# Define the entrypoint
ENTRYPOINT ["./entrypoint.sh"]