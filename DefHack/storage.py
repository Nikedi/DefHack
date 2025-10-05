import boto3
from .config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.MINIO_ENDPOINT,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
)

def put_object(key: str, data: bytes):
    _s3.put_object(Bucket=settings.MINIO_BUCKET, Key=key, Body=data)

def head_object(key: str):
    return _s3.head_object(Bucket=settings.MINIO_BUCKET, Key=key)