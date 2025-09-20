import boto3
from django.conf import settings

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
        return f"{bucket}/{file_name}"  
    except Exception as e:
        print("MinIO Upload Error:", e)
        return None


def get_presigned_url(file_key, expires_in=3600):

    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=expires_in
        )
        base_url = getattr(settings, "MEDIA_BASE_URL", settings.AWS_S3_ENDPOINT_URL)

        path = "/" + file_key
        return f"{base_url}{path}"
    except Exception as e:
        print("Error generating presigned URL:", e)
        return None
