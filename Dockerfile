FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

ENV BROWSER_PATH=/usr/bin/chromium

COPY app.py data_processor.py database.py pdf_export.py ./

RUN pip install --no-cache-dir \
    streamlit==1.32.0 \
    pandas==2.2.0 \
    plotly==5.18.0 \
    sqlalchemy==2.0.25 \
    psycopg2-binary==2.9.9 \
    reportlab==4.0.9 \
    kaleido==0.2.1 \
    matplotlib==3.8.2

RUN mkdir -p .streamlit && \
    echo "[server]" > .streamlit/config.toml && \
    echo "headless = true" >> .streamlit/config.toml && \
    echo "port = 5000" >> .streamlit/config.toml && \
    echo "address = \"0.0.0.0\"" >> .streamlit/config.toml && \
    echo "enableCORS = false" >> .streamlit/config.toml && \
    echo "enableXsrfProtection = false" >> .streamlit/config.toml

EXPOSE 5000

CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0"]
