
from typing import Any

from clinical_ai_pipeline.storage.s3_client import read_json_file


S3_KEY = "raw/medications/ddi-medication_100354_258163.json"


def profile_structure(
    data: Any,
    prefix: str = "",
    indent: int = 0,
) -> None:
    spacing = " " * indent

    if isinstance(data, dict):
        if not data:
            print(f"{spacing}{prefix}: empty object")
            return

        for key, value in data.items():
            field_name = f"{prefix}.{key}" if prefix else key
            profile_structure(value, field_name, indent)

    elif isinstance(data, list):
        print(
            f"{spacing}{prefix}: list "
            f"(length={len(data)})"
        )

        if not data:
            return

        for index, item in enumerate(data):
            item_prefix = f"{prefix}[{index}]"

            if isinstance(item, dict):
                print(f"{spacing}{item_prefix}: object")
                profile_structure(
                    item,
                    item_prefix,
                    indent + 2,
                )
            elif isinstance(item, list):
                profile_structure(
                    item,
                    item_prefix,
                    indent + 2,
                )
            else:
                print(
                    f"{spacing}{item_prefix}: "
                    f"{type(item).__name__}"
                )

    else:
        print(
            f"{spacing}{prefix}: "
            f"{type(data).__name__}"
        )


def main() -> None:
    data = read_json_file(S3_KEY)

    print("Complete JSON structure:")
    print("-" * 40)

    profile_structure(data)


if __name__ == "__main__":
    main()