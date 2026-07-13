import json
import os
from pathlib import Path

from google import genai
from google.genai import types

from msdat_aiprompts.exporters.csv_exporter import export_csv
from msdat_aiprompts.exporters.markdown_exporter import export_markdown
from msdat_aiprompts.exporters.testpod_csv_exporter import export_testpod_csv
from msdat_aiprompts.validators.test_case_validator import (
    validate_generated_tests,
)


BASE_DIR = Path(__file__).resolve().parents[2]

CONFIG_FILE = BASE_DIR / "config" / "ai_config.json"
PROMPT_FILE = BASE_DIR / "prompts" / "msdat_api_prompts.md"
INPUT_FILE = BASE_DIR / "inputs" / "api-endpoints.json"
OUTPUT_DIR = BASE_DIR / "outputs" / "generated-tests"


def load_json(file_path):
    return json.loads(file_path.read_text(encoding="utf-8"))


def load_prompt(file_path):
    return file_path.read_text(encoding="utf-8")


def build_prompt(prompt_template, item):
    final_prompt = prompt_template
    final_prompt = final_prompt.replace(
        "{{endpoint}}",
        item["endpoint"],
    )
    final_prompt = final_prompt.replace(
        "{{method}}",
        item["method"],
    )
    final_prompt = final_prompt.replace(
        "{{auth_required}}",
        str(item["auth_required"]),
    )
    final_prompt = final_prompt.replace(
        "{{auth_type}}",
        item.get("auth_type") or "None",
    )
    final_prompt = final_prompt.replace(
        "{{description}}",
        item["description"],
    )
    final_prompt = final_prompt.replace(
        "{{request_body}}",
        json.dumps(
            item.get("request_body"),
            indent=2,
        ),
    )

    return final_prompt


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

    start = cleaned.find("[")
    end = cleaned.rfind("]")

    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]

    return cleaned


def save_output(item, generated_tests):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_name = (
        item["name"]
        .lower()
        .replace(" ", "_")
    )

    json_file = OUTPUT_DIR / f"{base_name}.json"
    csv_file = OUTPUT_DIR / f"{base_name}.csv"
    markdown_file = OUTPUT_DIR / f"{base_name}.md"
    testpod_csv_file = (
        OUTPUT_DIR / f"{base_name}_testpod.csv"
    )

    json_file.write_text(
        generated_tests,
        encoding="utf-8",
    )

    export_csv(
        generated_tests,
        csv_file,
    )
    export_markdown(
        generated_tests,
        markdown_file,
    )
    export_testpod_csv(
        generated_tests,
        testpod_csv_file,
    )

    print(f"Generated JSON: {json_file}")
    print(f"Generated CSV: {csv_file}")
    print(f"Generated Markdown: {markdown_file}")
    print(
        f"Generated TestPod CSV: "
        f"{testpod_csv_file}"
    )


def generate_testpod_tests():
    config = load_json(CONFIG_FILE)
    prompt_template = load_prompt(PROMPT_FILE)
    endpoints = load_json(INPUT_FILE)

    max_endpoints = config.get(
        "max_endpoints_per_run"
    )

    if max_endpoints:
        endpoints = endpoints[:max_endpoints]

    for item in endpoints:
        final_prompt = build_prompt(
            prompt_template,
            item,
        )

        base_name = (
            item["name"]
            .lower()
            .replace(" ", "_")
        )

        json_file = (
            OUTPUT_DIR / f"{base_name}.json"
        )

        if json_file.exists():
            print(
                "Using existing generated JSON: "
                f"{json_file}"
            )

            generated_tests = json_file.read_text(
                encoding="utf-8"
            )
        else:
            print(
                "No existing JSON found. "
                f"Calling Gemini for: {item['name']}"
            )

            generated_tests = generate_with_gemini(
                config,
                final_prompt,
            )

            generated_tests = clean_ai_json(
                generated_tests
            )

        validate_generated_tests(
            generated_tests,
            minimum_test_cases=5,
        )

        save_output(
            item,
            generated_tests,
        )

    print(
        "AI TestPod test cases generated successfully."
    )
