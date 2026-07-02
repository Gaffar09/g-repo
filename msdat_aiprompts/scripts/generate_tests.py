import json
from pathlib import Path
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)


BASE_DIR = Path(__file__).resolve().parents[1]
prompt_template = (
    BASE_DIR / "prompts/msdat_api_prompts.md"
).read_text(encoding="utf-8")

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
    model="deepseek/deepseek-chat-v3",
    input=final_prompt
)

    file_name = item["name"].lower().replace(" ", "_") + "_tests.md"
    (output_dir / file_name).write_text(response.output_text)

print("AI test cases generated successfully.")
