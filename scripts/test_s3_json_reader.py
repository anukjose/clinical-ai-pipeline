from clinical_ai_pipeline.storage.s3_client import read_json_file


if __name__ == "__main__":
    s3_key = "raw/medications/ddi-medication_100354_258163.json"

    data = read_json_file(s3_key)

    print("Successfully read JSON file from S3.")
    print(f"Data type: {type(data).__name__}")

    if isinstance(data, dict):
        print(f"Top-level fields: {list(data.keys())}")