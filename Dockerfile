# syntax=docker/dockerfile:1
FROM python:3.13.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --system monitor && useradd --system --gid monitor --home-dir /app monitor
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x scripts/entrypoint.sh && chown -R monitor:monitor /app
USER monitor

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "goreecloud_monitor.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-"]
