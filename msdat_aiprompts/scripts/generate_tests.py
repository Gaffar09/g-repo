from msdat_aiprompts.validators.test_case_validator import validate_generated_tests
from msdat_aiprompts.exporters.csv_exporter import export_csv
from msdat_aiprompts.exporters.markdown_exporter import export_markdown
import os
import json
from pathlib import Path
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parents[1]

CONFIG_FILE = BASE_DIR / "config/ai_config.json"
PROMPT_FILE = BASE_DIR / "prompts/msdat_api_prompts.md"
INPUT_FILE = BASE_DIR / "inputs/api-endpoints.json"
OUTPUT_DIR = BASE_DIR / "outputs/generated-tests"


def load_json(file_path):
    return json.loads(file_path.read_text(encoding="utf-8"))


def load_prompt(file_path):
    return file_path.read_text(encoding="utf-8")


def build_prompt(prompt_template, item):
    final_prompt = prompt_template
    final_prompt = final_prompt.replace("{{endpoint}}", item["endpoint"])
    final_prompt = final_prompt.replace("{{method}}", item["method"])
    final_prompt = final_prompt.replace("{{auth_required}}", str(item["auth_required"]))
    final_prompt = final_prompt.replace("{{auth_type}}", item["auth_type"])
    final_prompt = final_prompt.replace("{{description}}", item["description"])
    final_prompt = final_prompt.replace(
        "{{request_body}}",
        json.dumps(item["request_body"], indent=2)
    )
    return final_prompt


def generate_with_gemini(config, prompt):
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    response = client.models.generate_content(
        model=config["model"],
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=config.get("temperature", 0.2)
        )
    )

    return response.text


def save_output(item, generated_tests):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base_name = item["name"].lower().replace(" ", "_")

    json_file = OUTPUT_DIR / f"{base_name}.json"
    csv_file = OUTPUT_DIR / f"{base_name}.csv"
    markdown_file = OUTPUT_DIR / f"{base_name}.md"

    # Save raw AI JSON output
    json_file.write_text(generated_tests, encoding="utf-8")

    # Export JSON into CSV and Markdown
    export_csv(generated_tests, csv_file)
    export_markdown(generated_tests, markdown_file)

    print(f"Generated JSON: {json_file}")
    print(f"Generated CSV: {csv_file}")
    print(f"Generated Markdown: {markdown_file}")

def main():
    config = load_json(CONFIG_FILE)
    prompt_template = load_prompt(PROMPT_FILE)
    endpoints = load_json(INPUT_FILE)

    for item in endpoints:
        final_prompt = build_prompt(prompt_template, item)
        generated_tests = generate_with_gemini(config, final_prompt)

        validate_generated_tests(
            generated_tests,
            minimum_test_cases=5
        )

        save_output(item, generated_tests)

    print("AI test cases generated successfully.")


if __name__ == "__main__":
    main()
