# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

ARG ENV=dev
ENV ENV=${ENV}

# Create working directory
WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . /app

# (Optionally) define default environment variables for local testing
# ENV MONGODB_URI="mongodb://host.docker.internal:27017/manuscript_db"

# Expose port 80 to the host
EXPOSE 80

# Command to run the app
CMD ["streamlit", "run", "home.py", "--server.port=80", "--server.address=0.0.0.0"]
