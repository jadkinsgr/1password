FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary files including db_utils.py
COPY app.py fetch_detailed_metadata.py db_utils.py ./

# Default command runs app.py, can be overridden in docker-compose
CMD ["python", "app.py"]