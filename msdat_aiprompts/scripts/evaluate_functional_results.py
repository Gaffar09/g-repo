import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG_FILE = BASE_DIR / "config" / "ai_config.json"
PROMPT_FILE = BASE_DIR / "prompts" / "msdat_functional_evaluation_prompt.md"
RESULT_FILE = BASE_DIR / "outputs" / "functional-results" / "newman_results.json"
OUTPUT_DIR = BASE_DIR / "outputs" / "functional-results"
EVALUATION_FILE = OUTPUT_DIR / "ai_functional_evaluation.json"


def load_json(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return json.loads(file_path.read_text(encoding="utf-8"))


def load_prompt(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    return file_path.read_text(encoding="utf-8")


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
            temperature=config.get("temperature", 0.2),
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text


def clean_ai_json(raw_text):
    cleaned = raw_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1).strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]

    return cleaned


def validate_evaluation(evaluation):
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
                f"AI evaluation is missing required section: {section}"
            )

    summary = evaluation["summary"]

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
                f"AI evaluation summary is missing field: {field}"
            )

    allowed_statuses = {"PASS", "FAIL", "PARTIAL"}

    if summary["overall_status"] not in allowed_statuses:
        raise ValueError(
            f"Invalid overall status: {summary['overall_status']}"
        )

    if not isinstance(summary["total_tests"], int):
        raise ValueError("total_tests must be an integer.")

    if not isinstance(summary["passed"], int):
        raise ValueError("passed must be an integer.")

    if not isinstance(summary["failed"], int):
        raise ValueError("failed must be an integer.")

    if not isinstance(summary["skipped"], int):
        raise ValueError("skipped must be an integer.")

    if not isinstance(summary["pass_rate"], (int, float)):
        raise ValueError("pass_rate must be a number.")

    if summary["total_tests"] > 0:
        calculated_pass_rate = (
            summary["passed"] / summary["total_tests"]
        ) * 100

        if abs(calculated_pass_rate - summary["pass_rate"]) > 0.1:
            raise ValueError(
                "AI-generated pass rate does not match test counts."
            )


def build_evaluation_prompt(prompt_template, newman_results):
    results_json = json.dumps(
        newman_results,
        indent=2
    )

    return (
        prompt_template
        + "\n\n==================================================\n"
        + "NEWMAN EXECUTION RESULTS\n"
        + "==================================================\n\n"
        + results_json
    )


def save_evaluation(evaluation):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    EVALUATION_FILE.write_text(
        json.dumps(evaluation, indent=2),
        encoding="utf-8",
    )

    print(f"AI evaluation saved to: {EVALUATION_FILE}")


def main():
    try:
        print("Starting AI evaluation of Newman functional results...")

        config = load_json(CONFIG_FILE)
        prompt_template = load_prompt(PROMPT_FILE)
        newman_results = load_json(RESULT_FILE)

        print(f"Reading Newman results: {RESULT_FILE}")

        final_prompt = build_evaluation_prompt(
            prompt_template,
            newman_results,
        )

        print("Sending Newman results to Gemini...")

        raw_response = generate_with_gemini(
            config,
            final_prompt,
        )

        cleaned_response = clean_ai_json(raw_response)

        try:
            evaluation = json.loads(cleaned_response)
        except json.JSONDecodeError as error:
            print("Gemini returned invalid JSON.")
            print(f"JSON error: {error}")

            invalid_file = (
                OUTPUT_DIR / "invalid_ai_evaluation_response.txt"
            )

            invalid_file.write_text(
                raw_response,
                encoding="utf-8",
            )

            print(
                f"Invalid AI response saved to: {invalid_file}"
            )

            raise

        validate_evaluation(evaluation)

        save_evaluation(evaluation)

        print(
            "AI functional evaluation completed successfully."
        )

    except Exception as error:
        print(
            f"AI functional evaluation failed: {error}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
