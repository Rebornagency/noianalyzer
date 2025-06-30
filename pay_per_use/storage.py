import os
import boto3
from typing import Tuple
from uuid import uuid4

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def upload_report(report_path: str, job_id: str) -> str:
    """Upload generated report to S3 and return object key."""
    object_key = f"reports/{job_id}/{os.path.basename(report_path)}"
    s3_client.upload_file(report_path, AWS_S3_BUCKET, object_key, ExtraArgs={"ACL": "private"})
    return object_key


def generate_presigned_url(object_key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for accessing the report."""
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": object_key},
        ExpiresIn=expires_in,
    )
    return url 