# 1. Start from a base Python image
FROM python:3.11-slim

# 2. Set working directory inside container
WORKDIR /app

# 3. Copy your project code into the container
#    (you can narrow this if needed)
COPY . /app

# 4. Install dependencies (if you have requirements.txt)
#    Comment this out if you don't need it.
# RUN pip install --no-cache-dir -r requirements.txt

# 5. Default command (can be overridden).
#    We'll override this when calling `docker run`, so this can be anything.
CMD ["python", "main.py"]
