from collections import Counter

from clinical_ai_pipeline.storage.s3_client import (
    list_medication_files,
    read_json_file,
)


def main() -> None:
    s3_keys = list_medication_files()

    section_types = Counter()
    data_field_patterns = Counter()
    total_sections = 0

    print(f"Analysing {len(s3_keys)} files...\n")

    for index, s3_key in enumerate(s3_keys, start=1):
        data = read_json_file(s3_key)

        for section in data.get("prescription", []):
            total_sections += 1

            section_type = (
                section.get("type"),
                section.get("typeLabel"),
                section.get("sectionName"),
            )

            section_types[section_type] += 1

            for item in section.get("data", []):
                field_pattern = tuple(sorted(item.keys()))
                data_field_patterns[field_pattern] += 1

        if index % 100 == 0:
            print(f"Processed {index}/{len(s3_keys)} files")

    print("\nSection Types")
    print("-" * 40)

    for section, count in section_types.most_common():
        print(f"{count} | {section}")

    print("\nData Field Patterns")
    print("-" * 40)

    for fields, count in data_field_patterns.most_common():
        print(f"{count} | {fields}")

    print(f"\nTotal sections analysed: {total_sections}")


if __name__ == "__main__":
    main()