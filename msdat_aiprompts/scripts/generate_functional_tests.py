import json
import os
from pathlib import Path

from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG_FILE = BASE_DIR / "config" / "ai_config.json"
PROMPT_FILE = (
    BASE_DIR
    / "prompts"
    / "msdat_functional_execution_prompt.md"
)
INPUT_FILE = BASE_DIR / "inputs" / "api-endpoints.json"
TEST_DATA_FILE = (
    BASE_DIR
    / "fixtures"
    / "reusable_test_data.json"
)
OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "generated-tests"
    / "functional"
)


def load_json(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return json.loads(
        file_path.read_text(encoding="utf-8")
    )


def load_prompt(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {file_path}"
        )

    prompt = file_path.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise ValueError(
            f"Prompt file is empty: {file_path}"
        )

    return prompt


def build_prompt(
    prompt_template,
    endpoint,
    reusable_test_data,
):
    return f"""
{prompt_template}

API DEFINITION:

{json.dumps(endpoint, indent=2)}

REUSABLE TEST DATA:

{json.dumps(reusable_test_data, indent=2)}
""".strip()


def generate_with_gemini(config, prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is missing."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=config["model"],
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=config.get(
                "temperature",
                0.2,
            ),
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    return response.text


def clean_ai_json(raw_text):
    cleaned = raw_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace(
            "```json",
            "",
            1,
        ).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace(
            "```",
            "",
            1,
        ).strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Gemini response does not contain a JSON object."
        )

    return cleaned[start:end + 1]


def validate_functional_output(data):
    required_fields = [
        "api_name",
        "module",
        "endpoint",
        "method",
        "auth_required",
        "test_cases",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(
                f"Missing required field: {field}"
            )

    if not isinstance(data["test_cases"], list):
        raise ValueError(
            "test_cases must be a list."
        )

    if not data["test_cases"]:
        raise ValueError(
            "No functional test cases were generated."
        )

    allowed_categories = {
        "Happy Path",
        "Boundary Value",
        "Negative/Error Scenario",
    }

    allowed_priorities = {
        "High",
        "Medium",
        "Low",
    }

    for index, test_case in enumerate(
        data["test_cases"],
        start=1,
    ):
        required_test_fields = [
            "test_id",
            "category",
            "scenario",
            "request",
            "expected_status",
            "expected_result",
            "assertions",
            "priority",
            "automation_tool",
        ]

        for field in required_test_fields:
            if field not in test_case:
                raise ValueError(
                    f"Test case {index} is missing: {field}"
                )

        if test_case["category"] not in allowed_categories:
            raise ValueError(
                f"Invalid category in test case {index}"
            )

        if test_case["priority"] not in allowed_priorities:
            raise ValueError(
                f"Invalid priority in test case {index}"
            )

        if not test_case["test_id"].startswith(
            "APIMSDAT-"
        ):
            raise ValueError(
                f"Invalid test ID in test case {index}"
            )

        request = test_case["request"]

        if not request.get("method"):
            raise ValueError(
                f"Request method missing in test case {index}"
            )

        if not request.get("url"):
            raise ValueError(
                f"Request URL missing in test case {index}"
            )

        assertions = test_case["assertions"]

        if not isinstance(assertions, list):
            raise ValueError(
                f"Assertions must be a list in test case {index}"
            )

        if not assertions:
            raise ValueError(
                f"No assertions found in test case {index}"
            )

        for assertion in assertions:
            if not assertion.get("name"):
                raise ValueError(
                    f"Assertion name missing in test case {index}"
                )

            if not assertion.get("script"):
                raise ValueError(
                    f"Assertion script missing in test case {index}"
                )


def create_file_name(name):
    return (
        name.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )


def save_output(endpoint, generated_data):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_name = create_file_name(
        endpoint["name"]
    )

    output_file = OUTPUT_DIR / f"{file_name}.json"

    output_file.write_text(
        json.dumps(
            generated_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Generated functional tests: {output_file}"
    )


def main():
    config = load_json(CONFIG_FILE)
    prompt_template = load_prompt(PROMPT_FILE)
    endpoints = load_json(INPUT_FILE)
    reusable_test_data = load_json(TEST_DATA_FILE)

    max_endpoints = config.get(
        "max_endpoints_per_run"
    )

    if max_endpoints:
        endpoints = endpoints[:max_endpoints]

    for endpoint in endpoints:
        print(
            f"Generating functional tests for: "
            f"{endpoint['name']}"
        )

        final_prompt = build_prompt(
            prompt_template,
            endpoint,
            reusable_test_data,
        )

        raw_response = generate_with_gemini(
            config,
            final_prompt,
        )

        cleaned_response = clean_ai_json(
            raw_response
        )

        generated_data = json.loads(
            cleaned_response
        )

        validate_functional_output(
            generated_data
        )

        save_output(
            endpoint,
            generated_data,
        )

    print(
        "Functional test generation completed successfully."
    )


if __name__ == "__main__":
    main()
