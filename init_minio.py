#!/usr/bin/env python3
import boto3
import sys
from botocore.exceptions import ClientError

def create_bucket():
    """Create the intel bucket in MinIO"""
    # MinIO connection settings
    s3_client = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minio',
        aws_secret_access_key='minio123',
        region_name='us-east-1'
    )
    
    bucket_name = 'intel'
    
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' already exists")
        return True
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            # Bucket doesn't exist, create it
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                print(f"✅ Successfully created bucket '{bucket_name}'")
                return True
            except ClientError as create_error:
                print(f"❌ Failed to create bucket '{bucket_name}': {create_error}")
                return False
        else:
            print(f"❌ Error checking bucket '{bucket_name}': {e}")
            return False

if __name__ == "__main__":
    print("Initializing MinIO bucket...")
    success = create_bucket()
    sys.exit(0 if success else 1)