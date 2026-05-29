# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry


# Copy the pyproject.toml and poetry.lock files to the container
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry install --no-root



# Copy the application code
COPY . /app

# Set up logger file
RUN mkdir /app/logs

# Expose the port that the app will run on
EXPOSE 8000

# Start FastAPI application with uvicorn
CMD ["poetry", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
