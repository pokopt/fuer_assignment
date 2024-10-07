# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /usr/src/app

# Set PYTHONPATH to the working directory
ENV PYTHONPATH=/usr/src/app

# Copy only requirements first to take advantage of Docker layer caching
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/local/bin/entrypoint.sh 

# Expose port 8080 for the web server
EXPOSE 8080

# Make sure the entrypoint script is executable
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint to the script
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]