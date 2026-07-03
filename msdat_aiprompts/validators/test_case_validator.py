import json


REQUIRED_FIELDS = [
    "test_id",
    "scenario",
    "precondition",
    "test_steps",
    "test_data",
    "expected_result",
    "priority",
    "automation_tool"
]

VALID_PRIORITIES = ["High", "Medium", "Low"]
VALID_AUTOMATION_TOOLS = ["Postman", "Newman", "k6"]


def validate_generated_tests(json_text, minimum_test_cases=5):
    errors = []

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON returned by AI: {error}")

    if not isinstance(data, list):
        raise ValueError("AI output must be a JSON array of test cases.")

    if len(data) < minimum_test_cases:
        errors.append(
            f"Expected at least {minimum_test_cases} test cases, but got {len(data)}."
        )

    seen_ids = set()

    for index, test_case in enumerate(data, start=1):
        if not isinstance(test_case, dict):
            errors.append(f"Test case at position {index} is not a JSON object.")
            continue

        for field in REQUIRED_FIELDS:
            if field not in test_case:
                errors.append(f"Test case {index} is missing required field: {field}")
            elif str(test_case[field]).strip() == "":
                errors.append(f"Test case {index} has empty field: {field}")

        test_id = test_case.get("test_id")

        if test_id:
            if test_id in seen_ids:
                errors.append(f"Duplicate test ID found: {test_id}")
            seen_ids.add(test_id)

            if not str(test_id).startswith("APIMSDAT-"):
                errors.append(
                    f"Test ID {test_id} must start with APIMSDAT-"
                )

        priority = test_case.get("priority")
        if priority and priority not in VALID_PRIORITIES:
            errors.append(
                f"Invalid priority '{priority}'. Allowed values: {VALID_PRIORITIES}"
            )

        automation_tool = test_case.get("automation_tool")
        if automation_tool and automation_tool not in VALID_AUTOMATION_TOOLS:
            errors.append(
                f"Invalid automation tool '{automation_tool}'. Allowed values: {VALID_AUTOMATION_TOOLS}"
            )

    if errors:
        raise ValueError("Validation failed:\n" + "\n".join(errors))

    return data
