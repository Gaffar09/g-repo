import os
import json
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1"
)

BASE_DIR = Path(__file__).resolve().parents[1]

prompt_template = (
    BASE_DIR / "prompts/msdat_api_prompts.md"
).read_text(encoding="utf-8")

endpoints = json.loads(
    (BASE_DIR / "inputs/api-endpoints.json").read_text(encoding="utf-8")
)

output_dir = BASE_DIR / "outputs/generated-tests"
output_dir.mkdir(parents=True, exist_ok=True)

for item in endpoints:

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

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3",
        messages=[
            {
                "role": "user",
                "content": final_prompt
            }
        ],
        temperature=0.2
    )

    generated_tests = response.choices[0].message.content

    file_name = item["name"].lower().replace(" ", "_") + "_tests.md"

    (output_dir / file_name).write_text(
        generated_tests,
        encoding="utf-8"
    )

print("AI test cases generated successfully.")
