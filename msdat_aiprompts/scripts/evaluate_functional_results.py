import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG_FILE = BASE_DIR / "config" / "ai_config.json"
PROMPT_FILE = BASE_DIR / "prompts" / "msdat_functional_evaluation_prompt.md"
RESULT_FILE = (
    BASE_DIR
    / "outputs"
    / "functional-results"
    / "newman_results.json"
)
OUTPUT_DIR = BASE_DIR / "outputs" / "functional-results"
EVALUATION_FILE = (
    OUTPUT_DIR / "ai_functional_evaluation.json"
)
EVIDENCE_FILE = (
    OUTPUT_DIR / "newman_evaluation_evidence.json"
)


def load_json(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )


def load_prompt(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {file_path}"
        )

    return file_path.read_text(
        encoding="utf-8"
    )


def safe_text(value, max_length=500):
    """
    Convert a value to safe, compact text.

    Long response bodies, tokens, HTML pages, and other
    noisy data are truncated.
    """
    if value is None:
        return ""

    text = str(value)

    if len(text) > max_length:
        return text[:max_length] + "...[truncated]"

    return text


def extract_endpoint(request):
    """
    Extract the request URL without exposing query values
    unnecessarily.
    """
    if not isinstance(request, dict):
        return ""

    url = request.get("url", "")

    if isinstance(url, dict):
        raw = url.get("raw", "")
        if raw:
            return safe_text(raw, 300)

        path = url.get("path", [])

        if isinstance(path, list):
            return "/" + "/".join(
                str(item)
                for item in path
            )

    return safe_text(url, 300)


def extract_assertion_failure(assertion):
    """
    Extract compact information about a failed assertion.
    """
    if not isinstance(assertion, dict):
        return {
            "name": "",
            "error": "",
        }

    return {
        "name": safe_text(
            assertion.get("assertion", ""),
            250,
        ),
        "error": safe_text(
            assertion.get("error", ""),
            500,
        ),
    }


def extract_execution_evidence(newman_results):
    """
    Convert the verbose Newman report into a compact,
    AI-friendly evidence structure.
    """

    run = newman_results.get("run", {})

    stats = run.get("stats", {})

    executions = run.get("executions", [])

    summary = {
        "total_requests": stats.get(
            "requests",
            {}
        ).get("total", 0),
        "failed_requests": stats.get(
            "requests",
            {}
        ).get("failed", 0),
        "total_test_scripts": stats.get(
            "testScripts",
            {}
        ).get("total", 0),
        "failed_test_scripts": stats.get(
            "testScripts",
            {}
        ).get("failed", 0),
        "total_assertions": stats.get(
            "assertions",
            {}
        ).get("total", 0),
        "failed_assertions": stats.get(
            "assertions",
            {}
        ).get("failed", 0),
    }

    total_assertions = summary["total_assertions"]
    failed_assertions = summary["failed_assertions"]

    passed_assertions = max(
        total_assertions - failed_assertions,
        0,
    )

    summary["passed_assertions"] = (
        passed_assertions
    )

    if total_assertions > 0:
        summary["assertion_pass_rate"] = round(
            (
                passed_assertions
                / total_assertions
            )
            * 100,
            2,
        )
    else:
        summary["assertion_pass_rate"] = 0

    failures = []
    test_results = []

    for execution in executions:
        item = execution.get("item", {})

        request = item.get(
            "request",
            {},
        )

        response = execution.get(
            "response",
            {},
        )

        assertions = execution.get(
            "assertions",
            [],
        )

        test_name = item.get(
            "name",
            "",
        )

        method = request.get(
            "method",
            "",
        )

        endpoint = extract_endpoint(
            request
        )

        response_code = (
            response.get("code")
            if isinstance(response, dict)
            else None
        )

        response_time = (
            response.get("responseTime")
            if isinstance(response, dict)
            else None
        )

        failed_for_test = []

        for assertion in assertions:
            if not isinstance(
                assertion,
                dict,
            ):
                continue

            error = assertion.get(
                "error"
            )

            if error:
                failure = {
                    "test_name": safe_text(
                        test_name,
                        300,
                    ),
                    "endpoint": endpoint,
                    "method": safe_text(
                        method,
                        20,
                    ),
                    "status_code": response_code,
                    "response_time_ms": response_time,
                    "failure": (
                        extract_assertion_failure(
                            assertion
                        )
                    ),
                }

                failures.append(
                    failure
                )

                failed_for_test.append(
                    failure["failure"]
                )

        test_results.append(
            {
                "test_name": safe_text(
                    test_name,
                    300,
                ),
                "endpoint": endpoint,
                "method": safe_text(
                    method,
                    20,
                ),
                "status_code": response_code,
                "response_time_ms": response_time,
                "failed_assertions": (
                    len(failed_for_test)
                ),
            }
        )

    evidence = {
        "summary": summary,
        "test_results": test_results,
        "failures": failures,
    }

    return evidence


def save_evidence(evidence):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EVIDENCE_FILE.write_text(
        json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Compact Newman evidence saved to: "
        f"{EVIDENCE_FILE}"
    )


def build_evaluation_prompt(
    prompt_template,
    evidence,
):
    evidence_json = json.dumps(
        evidence,
        indent=2,
        ensure_ascii=False,
    )

    return (
        prompt_template
        + "\n\n"
        + "==================================================\n"
        + "COMPACT NEWMAN EXECUTION EVIDENCE\n"
        + "==================================================\n\n"
        + evidence_json
        + "\n\n"
        + "IMPORTANT:\n"
        + "Base the evaluation only on the execution evidence "
        + "provided above. Do not invent missing results, "
        + "endpoints, failures, or API behavior."
    )


def generate_with_gemini(
    config,
    prompt,
):
    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable "
            "is missing."
        )

    client = genai.Client(
        api_key=api_key
    )

    max_attempts = 2

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        try:
            print(
                f"Gemini evaluation attempt "
                f"{attempt}/{max_attempts}..."
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

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED"
                in error_text
            ):
                if attempt < max_attempts:
                    retry_seconds = 45

                    print(
                        "Gemini quota limit reached."
                    )
                    print(
                        f"Waiting {retry_seconds} "
                        "seconds before retry..."
                    )

                    time.sleep(
                        retry_seconds
                    )

                    continue

            raise


def clean_ai_json(raw_text):
    cleaned = raw_text.strip()

    if cleaned.startswith(
        "```json"
    ):
        cleaned = cleaned.replace(
            "```json",
            "",
            1,
        ).strip()

    if cleaned.startswith(
        "```"
    ):
        cleaned = cleaned.replace(
            "```",
            "",
            1,
        ).strip()

    if cleaned.endswith(
        "```"
    ):
        cleaned = cleaned[:-3].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1:
        cleaned = cleaned[
            start : end + 1
        ]

    return cleaned


def validate_evaluation(
    evaluation,
    evidence,
):
    required_sections = [
        "summary",
        "failed_tests",
        "failure_patterns",
        "potential_defects",
        "security_observations",
        "recommendations",
    ]

    for section in required_sections:
        if section not in evaluation:
            raise ValueError(
                "AI evaluation is missing "
                f"required section: {section}"
            )

    summary = evaluation[
        "summary"
    ]

    required_summary_fields = [
        "overall_status",
        "total_tests",
        "passed",
        "failed",
        "skipped",
        "pass_rate",
    ]

    for field in required_summary_fields:
        if field not in summary:
            raise ValueError(
                "AI evaluation summary is "
                f"missing field: {field}"
            )

    allowed_statuses = {
        "PASS",
        "FAIL",
        "PARTIAL",
    }

    if summary[
        "overall_status"
    ] not in allowed_statuses:
        raise ValueError(
            "Invalid overall status: "
            f"{summary['overall_status']}"
        )

    for field in [
        "total_tests",
        "passed",
        "failed",
        "skipped",
    ]:
        if not isinstance(
            summary[field],
            int,
        ):
            raise ValueError(
                f"{field} must be an integer."
            )

    if not isinstance(
        summary["pass_rate"],
        (int, float),
    ):
        raise ValueError(
            "pass_rate must be a number."
        )

    total = summary[
        "total_tests"
    ]

    if total > 0:
        calculated_pass_rate = round(
            (
                summary["passed"]
                / total
            )
            * 100,
            2,
        )

        if abs(
            calculated_pass_rate
            - summary["pass_rate"]
        ) > 0.1:
            raise ValueError(
                "AI-generated pass rate "
                "does not match test counts."
            )


def save_evaluation(
    evaluation
):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    EVALUATION_FILE.write_text(
        json.dumps(
            evaluation,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"AI evaluation saved to: "
        f"{EVALUATION_FILE}"
    )


def main():
    try:
        print(
            "Starting AI evaluation of "
            "Newman functional results..."
        )

        config = load_json(
            CONFIG_FILE
        )

        prompt_template = load_prompt(
            PROMPT_FILE
        )

        newman_results = load_json(
            RESULT_FILE
        )

        print(
            f"Reading Newman results: "
            f"{RESULT_FILE}"
        )

        evidence = (
            extract_execution_evidence(
                newman_results
            )
        )

        save_evidence(
            evidence
        )

        print(
            "\nNewman execution summary:"
        )

        print(
            f"Requests: "
            f"{evidence['summary']['total_requests']}"
        )

        print(
            f"Failed requests: "
            f"{evidence['summary']['failed_requests']}"
        )

        print(
            f"Assertions: "
            f"{evidence['summary']['total_assertions']}"
        )

        print(
            f"Failed assertions: "
            f"{evidence['summary']['failed_assertions']}"
        )

        print(
            f"Assertion pass rate: "
            f"{evidence['summary']['assertion_pass_rate']}%"
        )

        final_prompt = (
            build_evaluation_prompt(
                prompt_template,
                evidence,
            )
        )

        print(
            "\nSending compact Newman "
            "evidence to Gemini..."
        )

        raw_response = (
            generate_with_gemini(
                config,
                final_prompt,
            )
        )

        cleaned_response = (
            clean_ai_json(
                raw_response
            )
        )

        try:
            evaluation = json.loads(
                cleaned_response
            )

        except json.JSONDecodeError as error:
            print(
                "Gemini returned invalid JSON."
            )
            print(
                f"JSON error: {error}"
            )

            invalid_file = (
                OUTPUT_DIR
                / "invalid_ai_evaluation_response.txt"
            )

            invalid_file.write_text(
                raw_response,
                encoding="utf-8",
            )

            print(
                "Invalid AI response saved to: "
                f"{invalid_file}"
            )

            raise

        validate_evaluation(
            evaluation,
            evidence,
        )

        save_evaluation(
            evaluation
        )

        print(
            "\nAI functional evaluation "
            "completed successfully."
        )

    except Exception as error:
        print(
            "\nAI functional evaluation "
            f"failed: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
