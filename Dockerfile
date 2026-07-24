# Python 3.11 base image එක
FROM python:3.11-slim

# Working directory එක set කරන්න
WORKDIR /app

# Backend dependencies copy කරන්න
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code එක copy කරන්න
COPY backend/ ./backend/
COPY protos/ ./protos/

# Port expose කරන්න
EXPOSE 10000

# App එක run කරන්න
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
