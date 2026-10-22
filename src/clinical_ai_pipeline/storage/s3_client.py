import boto3
import json

import json

from botocore.exceptions import BotoCoreError, ClientError

from clinical_ai_pipeline.config.settings import settings


def get_s3_client():
    """Create and return an AWS S3 client."""
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
    )


def list_medication_files():
    """List all medication JSON files from the configured S3 prefix."""
    s3_client = get_s3_client()

    paginator = s3_client.get_paginator("list_objects_v2")

    files = []

    for page in paginator.paginate(
        Bucket=settings.s3_bucket_name,
        Prefix=settings.s3_raw_prefix,
    ):
        for item in page.get("Contents", []):
            key = item["Key"]

            if key.endswith(".json"):
                files.append(key)

    return files



def read_json_file(s3_key: str) -> dict:
    """Read a JSON object from S3 and return it as a dictionary."""
    s3_client = get_s3_client()

    try:
        response = s3_client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
        )

        content = response["Body"].read()
        data = json.loads(content)

        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object, but received {type(data).__name__}"
            )

        return data

    except (ClientError, BotoCoreError) as error:
        raise RuntimeError(
            f"Failed to read S3 object: {s3_key}"
        ) from error

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON content in S3 object: {s3_key}"
        ) from error