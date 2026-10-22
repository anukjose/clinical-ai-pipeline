
from clinical_ai_pipeline.storage.s3_client import read_json_file
from clinical_ai_pipeline.processing.models import MedicationRecord


S3_KEY = "raw/medications/ddi-medication_100354_258163.json"


def main() -> None:
    data = read_json_file(S3_KEY)

    medication = MedicationRecord.model_validate(data)

    print("Pydantic validation successful!")
    print(f"Medication ID: {medication.medicationId}")
    print(f"Doctor department: {medication.doctor.departmentName}")
    print(f"Prescription sections: {len(medication.prescription)}")


if __name__ == "__main__":
    main()