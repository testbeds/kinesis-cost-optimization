#!/bin/bash
# Script to create an S3 bucket for Terraform backend
# If the bucket already exists, it returns the bucket name
# If the bucket does not exist, it creates a private bucket

set -e

# Check if bucket name is provided
if [ -z "$1" ]; then
    echo "Error: Bucket name is required"
    echo "Usage: $0 <bucket-name> <region>"
    exit 1
fi

# Check if region is provided
if [ -z "$2" ]; then
    echo "Error: Region is required"
    echo "Usage: $0 <bucket-name> <region>"
    exit 1
fi

BUCKET_NAME="$1"
REGION="$2"

echo "Checking if bucket '$BUCKET_NAME' exists..."

# Check if bucket exists
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "Bucket '$BUCKET_NAME' already exists"
    echo "$BUCKET_NAME"
    exit 0
fi

echo "Bucket '$BUCKET_NAME' does not exist. Creating..."

# Create the bucket
# Note: For us-east-1, we don't specify LocationConstraint
if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION"
else
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"
fi

echo "Bucket '$BUCKET_NAME' created successfully"

# Block all public access (make bucket private)
echo "Configuring bucket to block all public access..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Enable versioning for state file protection
echo "Enabling versioning on bucket..."
aws s3api put-bucket-versioning \
    --bucket "$BUCKET_NAME" \
    --versioning-configuration Status=Enabled

# Enable server-side encryption by default
echo "Enabling default encryption..."
aws s3api put-bucket-encryption \
    --bucket "$BUCKET_NAME" \
    --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'

echo "Bucket '$BUCKET_NAME' is ready for Terraform backend"
echo "$BUCKET_NAME"
