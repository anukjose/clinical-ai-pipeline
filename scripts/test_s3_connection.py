from clinical_ai_pipeline.storage.s3_client import list_medication_files

if __name__ == "__main__":
    files = list_medication_files()

    print(f"Found {len(files)} JSON files in S3.")

    for file_key in files[:5]:
        print(file_key)