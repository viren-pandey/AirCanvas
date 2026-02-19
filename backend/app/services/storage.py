from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import quote

try:
    import boto3
except ImportError:  # pragma: no cover - optional runtime dependency
    boto3 = None

from ..config import settings


class StorageService:
    """Object storage helper for signed upload/download URL generation."""

    def __init__(self) -> None:
        kwargs = {
            "region_name": settings.s3_region,
        }
        if settings.s3_access_key_id:
            kwargs["aws_access_key_id"] = settings.s3_access_key_id
        if settings.s3_secret_access_key:
            kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url

        self._bucket = settings.s3_bucket
        self._client = None
        if boto3 is not None:
            self._client = boto3.client("s3", **kwargs)

    @property
    def bucket(self) -> str:
        return self._bucket

    def build_frame_key(self, user_id: uuid.UUID, extension: str = "png") -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        suffix = uuid.uuid4().hex[:10]
        ext = extension.strip(".").lower() or "png"
        return f"users/{user_id}/frames/{user_id}_{ts}_{suffix}.{ext}"

    def build_thumbnail_key(self, user_id: uuid.UUID, extension: str = "jpg") -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        suffix = uuid.uuid4().hex[:10]
        ext = extension.strip(".").lower() or "jpg"
        return f"users/{user_id}/thumbnails/{user_id}_{ts}_{suffix}.{ext}"

    def object_uri(self, object_key: str) -> str:
        return f"s3://{self._bucket}/{object_key}"

    def key_from_uri(self, object_uri: str) -> str:
        prefix = f"s3://{self._bucket}/"
        if not object_uri.startswith(prefix):
            raise ValueError(f"Object URI does not belong to configured bucket: {object_uri}")
        return object_uri[len(prefix) :]

    def generate_upload_url(self, object_key: str, content_type: str) -> str:
        if self._client is not None:
            try:
                return self._client.generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": self._bucket,
                        "Key": object_key,
                        "ContentType": content_type,
                    },
                    ExpiresIn=settings.signed_url_ttl_seconds,
                )
            except Exception:
                pass
        return self._fallback_object_url(object_key)

    def generate_download_url(self, object_key: str) -> str:
        if self._client is not None:
            try:
                return self._client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self._bucket, "Key": object_key},
                    ExpiresIn=settings.signed_url_ttl_seconds,
                )
            except Exception:
                pass
        return self._fallback_object_url(object_key)

    def generate_download_url_from_uri(self, object_uri: str) -> str:
        if not object_uri:
            return ""
        key = self.key_from_uri(object_uri)
        return self.generate_download_url(key)

    def _fallback_object_url(self, object_key: str) -> str:
        escaped_key = quote(object_key, safe="/")
        if settings.s3_endpoint_url:
            endpoint = settings.s3_endpoint_url.rstrip("/")
            return f"{endpoint}/{self._bucket}/{escaped_key}"
        return f"https://{self._bucket}.s3.{settings.s3_region}.amazonaws.com/{escaped_key}"


storage_service = StorageService()
