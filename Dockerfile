FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY analytics.py .
COPY firebase_setup.py .

# Create directory for Streamlit config
RUN mkdir -p .streamlit

# Add Streamlit config
RUN echo '\
[theme]\n\
primaryColor = "#00a8a8"\n\
backgroundColor = "#FFFFFF"\n\
secondaryBackgroundColor = "#f0f2f6"\n\
textColor = "#262730"\n\
font = "sans serif"\n\
\n\
[server]\n\
port = 8501\n\
address = "0.0.0.0"\n\
headless = true\n\
maxUploadSize = 50\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
' > .streamlit/config.toml

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]