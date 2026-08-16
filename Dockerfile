FROM python:3.13-slim

RUN useradd --create-home appuser

WORKDIR /home/appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
