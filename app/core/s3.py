import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

def generate_presigned_upload_url(object_key: str, expiration: int = 3600) -> Optional[str]:
    """
    Generate a presigned URL to upload a file to S3.
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': object_key,
                'ContentType': 'application/pdf' # Defaulting to PDF but can be dynamic
            },
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None
    return response

def generate_presigned_download_url(object_key: str, expiration: int = 3600) -> Optional[str]:
    """
    Generate a presigned URL to download a file from S3.
    """
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': object_key
            },
            ExpiresIn=expiration
        )
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None
    return response
