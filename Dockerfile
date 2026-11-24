FROM python:3.12-slim

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m venv "$VIRTUAL_ENV"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py seed.py ./
COPY templates ./templates
COPY static ./static

EXPOSE 5000

CMD ["python", "app.py"]
