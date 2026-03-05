# MLflow with S3 (MinIO) + PostgreSQL support
FROM ghcr.io/mlflow/mlflow:v3.10.0

RUN pip install --no-cache-dir \
    boto3==1.34.0 \
    psycopg2-binary==2.9.9

EXPOSE 5000
