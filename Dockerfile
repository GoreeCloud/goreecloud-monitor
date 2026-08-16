# syntax=docker/dockerfile:1
FROM python:3.13.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd --system monitor && useradd --system --gid monitor --home-dir /app monitor
WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip check \
    && python -m pip uninstall --yes pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13

COPY . .
RUN chmod +x scripts/entrypoint.sh && chown -R monitor:monitor /app
USER monitor

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "goreecloud_monitor.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-"]
