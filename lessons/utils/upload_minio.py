import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, ClientError


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=getattr(settings, "AWS_REGION", None),
    )


def upload_file_to_minio(file_obj, file_name, bucket=None):

    bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
    s3_client = get_s3_client()

    try:
        s3_client.upload_fileobj(file_obj, bucket, file_name)
        return file_name
    except (NoCredentialsError, ClientError) as e:
        print("MinIO Upload Error:", e)
        return None



def get_presigned_url(file_key, expires_in=3600):
    file_key = file_key.lstrip("/")
    bucket_prefix = f"{settings.AWS_STORAGE_BUCKET_NAME}/"
    if file_key.startswith(bucket_prefix):
        file_key = file_key[len(bucket_prefix):]

    s3_client = get_s3_client()

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": file_key,
                "ResponseContentDisposition": "inline",
                "ResponseContentType": "image/jpeg",
            },
            ExpiresIn=expires_in,
        )

        public_url = url.replace(
            settings.AWS_S3_ENDPOINT_URL,
            settings.AWS_S3_PUBLIC_URL
        )
        return public_url
    except Exception as e:
        print("Presigned URL Error:", e)
        return None


def get_public_url(file_key):

    file_key = file_key.lstrip("/")
    bucket_prefix = f"{settings.AWS_STORAGE_BUCKET_NAME}/"
    if file_key.startswith(bucket_prefix):
        file_key = file_key[len(bucket_prefix):]

    return f"{settings.AWS_S3_PUBLIC_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{file_key}"
