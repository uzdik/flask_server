# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install \
    && rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget -N https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip -P /tmp && \
    unzip /tmp/chromedriver_linux64.zip -d /tmp && \
    rm /tmp/chromedriver_linux64.zip && \
    mv -f /tmp/chromedriver /usr/local/bin/chromedriver && \
    chmod 0755 /usr/local/bin/chromedriver

# Copy the current directory contents into the container at /app.
COPY . /app

# Install any needed packages specified in requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container.
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run app.py when the container launches.
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
