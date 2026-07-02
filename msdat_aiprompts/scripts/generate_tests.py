import os
import json
from pathlib import Path
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

BASE_DIR = Path(__file__).resolve().parents[1]

prompt_template = (BASE_DIR / "prompts/api-test-generation.md").read_text()
endpoints = json.loads((BASE_DIR / "inputs/api-endpoints.json").read_text())

output_dir = BASE_DIR / "outputs/generated-tests"
output_dir.mkdir(parents=True, exist_ok=True)

for item in endpoints:
    final_prompt = prompt_template
    final_prompt = final_prompt.replace("{{endpoint}}", item["endpoint"])
    final_prompt = final_prompt.replace("{{method}}", item["method"])
    final_prompt = final_prompt.replace("{{auth_required}}", str(item["auth_required"]))
    final_prompt = final_prompt.replace("{{request_body}}", json.dumps(item["request_body"], indent=2))

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=final_prompt
    )

    file_name = item["name"].lower().replace(" ", "_") + "_tests.md"
    (output_dir / file_name).write_text(response.output_text)

print("AI test cases generated successfully.")
