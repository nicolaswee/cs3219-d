import boto3
import os

class S3File:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.environ['S3_KEY'],
        aws_secret_access_key=os.environ['S3_SECRET_ACCESS_KEY']
    )

    def __init__(self, S3_BUCKET):
        self.S3_BUCKET = S3_BUCKET

    def upload_file_to_s3(self, file, formatted_file_name):

        try:
            self.s3_client.upload_fileobj(
                Key=formatted_file_name,
                Bucket=self.S3_BUCKET,
                Fileobj=file
            )
        except Exception as e:
            raise e

    def delete_file_to_s3(self, formatted_file_name):

        try:
            self.s3_client.delete_object(
                Bucket=self.S3_BUCKET,
                Key=formatted_file_name
            )
        except Exception as e:
            raise e
