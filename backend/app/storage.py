from __future__ import annotations

import io
from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from app.config import get_settings


@lru_cache
def get_client() -> Minio:
    s = get_settings()
    client = Minio(
        s.minio_endpoint,
        access_key=s.minio_root_user,
        secret_key=s.minio_root_password,
        secure=s.minio_use_ssl,
    )
    if not client.bucket_exists(s.minio_bucket):
        client.make_bucket(s.minio_bucket)
    return client


def put_object(key: str, data: bytes, content_type: str = "application/pdf") -> None:
    s = get_settings()
    client = get_client()
    client.put_object(
        s.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def get_object_bytes(key: str) -> bytes:
    s = get_settings()
    client = get_client()
    response = client.get_object(s.minio_bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def object_exists(key: str) -> bool:
    s = get_settings()
    client = get_client()
    try:
        client.stat_object(s.minio_bucket, key)
        return True
    except S3Error:
        return False
