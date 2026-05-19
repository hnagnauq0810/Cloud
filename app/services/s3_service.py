import io
import mimetypes
import uuid
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings, get_settings


class S3ConfigurationError(RuntimeError):
    pass


class S3UploadError(RuntimeError):
    pass


@dataclass(frozen=True)
class S3UploadResult:
    bucket: str
    key: str


class S3Service:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.s3_bucket_name:
            raise S3ConfigurationError("S3_BUCKET_NAME is not configured")
        client_kwargs = {"region_name": self.settings.aws_region}
        if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.settings.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.settings.aws_secret_access_key
            if self.settings.aws_session_token:
                client_kwargs["aws_session_token"] = self.settings.aws_session_token

        self.client = boto3.client("s3", **client_kwargs)
        self.bucket_name = self.settings.s3_bucket_name

    def build_object_key(self, filename: str) -> str:
        safe_filename = filename.replace("/", "_").replace("\\", "_") or "uploaded-file"
        unique_id = uuid.uuid4().hex
        return f"{self.settings.s3_upload_prefix}/{unique_id}-{safe_filename}"

    def upload_bytes(self, *, content: bytes, filename: str, content_type: str | None = None) -> S3UploadResult:
        key = self.build_object_key(filename)
        guessed_type = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        try:
            self.client.upload_fileobj(
                io.BytesIO(content),
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": guessed_type},
            )
        except (BotoCoreError, ClientError) as exc:
            raise S3UploadError(f"Failed to upload file to S3: {exc}") from exc

        return S3UploadResult(bucket=self.bucket_name, key=key)

    def create_presigned_download_url(self, *, key: str) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=self.settings.presigned_url_expiration_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            raise S3UploadError(f"Failed to create presigned URL: {exc}") from exc

    def check_bucket_access(self) -> bool:
        try:
            self.client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            return True
        except (BotoCoreError, ClientError):
            return False
