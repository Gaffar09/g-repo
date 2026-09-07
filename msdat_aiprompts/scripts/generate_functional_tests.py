import json
import os
import sys
import time
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


def create_file_name(name):
    return (
        name.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("-", "_")
    )


def get_output_file(endpoint_name):
    file_name = create_file_name(endpoint_name)

    return OUTPUT_DIR / f"{file_name}.json"


def existing_output_is_valid(output_file):
    """
    Check whether an existing generated test file
    contains valid, usable functional test data.
    """

    if not output_file.exists():
        return False

    try:
        existing_data = json.loads(
            output_file.read_text(
                encoding="utf-8"
            )
        )

        validate_functional_output(
            existing_data
        )

        return True

    except (
        json.JSONDecodeError,
        OSError,
        ValueError,
        TypeError,
    ):
        return False


def generate_with_gemini(config, prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is missing."
        )

    client = genai.Client(api_key=api_key)

    max_attempts = 4

    retry_delays = [
        30,
        60,
        120,
    ]

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            print(
                f"Sending request to Gemini "
                f"(attempt {attempt}/{max_attempts})..."
            )

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

        except Exception as error:
            error_text = str(error)

            is_retryable = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            )

            if not is_retryable:
                raise

            if attempt == max_attempts:
                print(
                    "Gemini request failed after "
                    f"{max_attempts} attempts."
                )

                raise

            delay = retry_delays[
                attempt - 1
            ]

            print(
                "Gemini temporarily unavailable "
                "or rate limited."
            )

            print(
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)


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
            "Gemini response does not contain "
            "a JSON object."
        )

    return cleaned[
        start:end + 1
    ]


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

    if not isinstance(
        data["test_cases"],
        list,
    ):
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
                    f"Test case {index} "
                    f"is missing: {field}"
                )

        if (
            test_case["category"]
            not in allowed_categories
        ):
            raise ValueError(
                f"Invalid category in "
                f"test case {index}"
            )

        if (
            test_case["priority"]
            not in allowed_priorities
        ):
            raise ValueError(
                f"Invalid priority in "
                f"test case {index}"
            )

        if not test_case[
            "test_id"
        ].startswith("APIMSDAT-"):
            raise ValueError(
                f"Invalid test ID in "
                f"test case {index}"
            )

        request = test_case["request"]

        if not request.get("method"):
            raise ValueError(
                f"Request method missing in "
                f"test case {index}"
            )

        if not request.get("url"):
            raise ValueError(
                f"Request URL missing in "
                f"test case {index}"
            )

        assertions = test_case[
            "assertions"
        ]

        if not isinstance(
            assertions,
            list,
        ):
            raise ValueError(
                f"Assertions must be a list "
                f"in test case {index}"
            )

        if not assertions:
            raise ValueError(
                f"No assertions found in "
                f"test case {index}"
            )

        for assertion in assertions:
            if not assertion.get("name"):
                raise ValueError(
                    f"Assertion name missing "
                    f"in test case {index}"
                )

            if not assertion.get("script"):
                raise ValueError(
                    f"Assertion script missing "
                    f"in test case {index}"
                )


def save_output(
    endpoint,
    generated_data,
):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = get_output_file(
        endpoint["name"]
    )

    output_file.write_text(
        json.dumps(
            generated_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Generated functional tests: "
        f"{output_file}"
    )


def main():
    print(
        "Starting MSDAT functional "
        "test generation..."
    )

    config = load_json(
        CONFIG_FILE
    )

    prompt_template = load_prompt(
        PROMPT_FILE
    )

    endpoints = load_json(
        INPUT_FILE
    )

    reusable_test_data = load_json(
        TEST_DATA_FILE
    )

    max_endpoints = config.get(
        "max_endpoints_per_run"
    )

    if max_endpoints:
        endpoints = endpoints[
            :max_endpoints
        ]

    generated_count = 0
    skipped_count = 0

    print(
        f"Endpoints to process: "
        f"{len(endpoints)}"
    )

    for endpoint in endpoints:
        endpoint_name = endpoint[
            "name"
        ]

        output_file = get_output_file(
            endpoint_name
        )

        print(
            "\n----------------------------------------"
        )

        print(
            f"Processing: {endpoint_name}"
        )

        # --------------------------------------------------
        # STEP 1: Check for an existing valid result
        # --------------------------------------------------

        if existing_output_is_valid(
            output_file
        ):
            print(
                "Valid existing functional "
                "tests found."
            )

            print(
                f"Skipping AI generation: "
                f"{output_file}"
            )

            skipped_count += 1

            continue

        # --------------------------------------------------
        # STEP 2: Generate tests with Gemini
        # --------------------------------------------------

        print(
            f"Generating functional tests "
            f"for: {endpoint_name}"
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

        # --------------------------------------------------
        # STEP 3: Clean AI response
        # --------------------------------------------------

        cleaned_response = clean_ai_json(
            raw_response
        )

        # --------------------------------------------------
        # STEP 4: Parse JSON
        # --------------------------------------------------

        try:
            generated_data = json.loads(
                cleaned_response
            )

        except json.JSONDecodeError as error:
            invalid_file = (
                OUTPUT_DIR
                / (
                    f"{create_file_name(endpoint_name)}"
                    "_invalid_response.txt"
                )
            )

            OUTPUT_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            invalid_file.write_text(
                raw_response,
                encoding="utf-8",
            )

            print(
                "Gemini returned invalid JSON."
            )

            print(
                f"Invalid response saved to: "
                f"{invalid_file}"
            )

            raise ValueError(
                f"Invalid JSON returned by Gemini "
                f"for {endpoint_name}: {error}"
            )

        # --------------------------------------------------
        # STEP 5: Validate generated tests
        # --------------------------------------------------

        validate_functional_output(
            generated_data
        )

        # --------------------------------------------------
        # STEP 6: Save generated tests
        # --------------------------------------------------

        save_output(
            endpoint,
            generated_data,
        )

        generated_count += 1

    print(
        "\n========================================"
    )

    print(
        "Functional test generation completed."
    )

    print(
        f"Newly generated: {generated_count}"
    )

    print(
        f"Skipped existing: {skipped_count}"
    )

    print(
        f"Total processed: {len(endpoints)}"
    )

    print(
        "========================================"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            "\nFunctional test generation failed:"
        )

        print(error)

        sys.exit(1)
