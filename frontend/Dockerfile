# frontend/Dockerfile

# Use official Python image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY frontend/requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY frontend/streamlit_app /app/streamlit_app

# Expose port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "streamlit_app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
