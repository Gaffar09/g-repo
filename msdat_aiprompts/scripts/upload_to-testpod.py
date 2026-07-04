import os
import json
from pathlib import Path
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
GENERATED_TESTS_DIR = BASE_DIR / "outputs/generated-tests"

TESTPOD_API_URL = "https://api.testpod.io/api"
TESTPOD_PROJECT_ID = "a2296702-c5e2-4139-a487-6202f2fbd409"
TESTPOD_TOKEN = os.environ["TESTPOD_API_TOKEN"]


def html_wrap(value):
    value = str(value or "").strip()
    return f"<p>{value}</p>"


def upload_test_case(test_case):
    url = f"{TESTPOD_API_URL}/projects/{TESTPOD_PROJECT_ID}/test-cases/"

    payload = {
        "requirement_tool": "",
        "name": test_case.get("scenario", ""),
        "state": "",
        "priority": test_case.get("priority", "").lower(),
        "automation_status": "automation not required",
        "type": "api",
        "description": html_wrap(test_case.get("scenario", "")),
        "precondition": html_wrap(test_case.get("precondition", "")),
        "step_type": "document",
        "expected_result": html_wrap(test_case.get("expected_result", "")),
        "steps": html_wrap(test_case.get("test_steps", ""))
    }

    headers = {
        "Authorization": f"Bearer {TESTPOD_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code not in [200, 201]:
        print("Failed payload:")
        print(json.dumps(payload, indent=2))
        print("Response:")
        print(response.text)
        response.raise_for_status()

    result = response.json()
    print(f"Uploaded: {test_case.get('test_id')} - {test_case.get('scenario')}")
    return result


def main():
    json_files = list(GENERATED_TESTS_DIR.glob("*.json"))

    if not json_files:
        raise FileNotFoundError("No generated JSON test files found.")

    for json_file in json_files:
        print(f"Uploading test cases from: {json_file}")

        test_cases = json.loads(json_file.read_text(encoding="utf-8"))

        for test_case in test_cases:
            upload_test_case(test_case)

    print("All generated test cases uploaded to TestPod successfully.")


if __name__ == "__main__":
    main()
