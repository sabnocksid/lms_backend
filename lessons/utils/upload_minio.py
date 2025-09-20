import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError

def upload_file_to_minio(file_obj, file_name, bucket=None):
    bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    try:
        s3_client.upload_fileobj(file_obj, bucket, file_name)
        return file_name  
    except (NoCredentialsError, ClientError) as e:
        print("MinIO Upload Error:", e)
        return None


def get_public_url(file_key):
    file_key = file_key.lstrip('/')
    return f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{file_key}"
