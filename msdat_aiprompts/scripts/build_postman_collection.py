import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

FUNCTIONAL_TESTS_DIR = (
    BASE_DIR
    / "outputs"
    / "generated-tests"
    / "functional"
)

COLLECTION_OUTPUT = (
    BASE_DIR
    / "postman"
    / "collections"
    / "msdat_functional_tests.postman_collection.json"
)


def load_json(file_path):
    return json.loads(
        file_path.read_text(encoding="utf-8")
    )


def save_json(file_path, data):
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def convert_headers(headers):
    return [
        {
            "key": key,
            "value": str(value),
            "type": "text",
        }
        for key, value in headers.items()
    ]


def convert_query_parameters(query_parameters):
    return [
        {
            "key": key,
            "value": str(value),
        }
        for key, value in query_parameters.items()
    ]


def build_request_body(request_data):
    body_mode = request_data.get(
        "body_mode",
        "none",
    )

    request_body = request_data.get(
        "request_body"
    )

    if body_mode == "none":
        return None

    if body_mode == "raw":
        if isinstance(request_body, str):
            raw_body = request_body
        else:
            raw_body = json.dumps(
                request_body,
                indent=2,
                ensure_ascii=False,
            )

        return {
            "mode": "raw",
            "raw": raw_body,
            "options": {
                "raw": {
                    "language": "json"
                }
            },
        }

    if body_mode == "urlencoded":
        if not isinstance(request_body, dict):
            return {
                "mode": "urlencoded",
                "urlencoded": [],
            }

        return {
            "mode": "urlencoded",
            "urlencoded": [
                {
                    "key": key,
                    "value": str(value),
                    "type": "text",
                }
                for key, value in request_body.items()
            ],
        }

    if body_mode == "formdata":
        if not isinstance(request_body, dict):
            return {
                "mode": "formdata",
                "formdata": [],
            }

        return {
            "mode": "formdata",
            "formdata": [
                {
                    "key": key,
                    "value": str(value),
                    "type": "text",
                }
                for key, value in request_body.items()
            ],
        }

    return None


def build_url(request_data):
    raw_url = request_data["url"]

    query_parameters = request_data.get(
        "query_parameters",
        {},
    )

    return {
        "raw": raw_url,
        "host": [
            "{{base_url}}"
        ],
        "query": convert_query_parameters(
            query_parameters
        ),
    }


def build_assertion_event(assertions):
    assertion_scripts = []

    for assertion in assertions:
        script = assertion.get(
            "script",
            "",
        ).strip()

        if script:
            assertion_scripts.extend(
                script.splitlines()
            )

    return {
        "listen": "test",
        "script": {
            "type": "text/javascript",
            "exec": assertion_scripts,
        },
    }


def convert_test_case(test_case):
    request_data = test_case["request"]

    postman_request = {
        "name": (
            f"{test_case['test_id']} - "
            f"{test_case['scenario']}"
        ),
        "request": {
            "method": request_data["method"],
            "header": convert_headers(
                request_data.get(
                    "headers",
                    {},
                )
            ),
            "url": build_url(
                request_data
            ),
        },
        "event": [
            build_assertion_event(
                test_case["assertions"]
            )
        ],
    }

    request_body = build_request_body(
        request_data
    )

    if request_body is not None:
        postman_request["request"]["body"] = (
            request_body
        )

    return postman_request


def build_collection():
    if not FUNCTIONAL_TESTS_DIR.exists():
        raise FileNotFoundError(
            "Functional test output folder "
            f"does not exist: {FUNCTIONAL_TESTS_DIR}"
        )

    functional_files = sorted(
        FUNCTIONAL_TESTS_DIR.glob("*.json")
    )

    if not functional_files:
        raise FileNotFoundError(
            "No functional test JSON files found in "
            f"{FUNCTIONAL_TESTS_DIR}"
        )

    collection = {
        "info": {
            "name": "MSDAT AI Functional Tests",
            "description": (
                "AI-generated functional API tests "
                "for MSDAT endpoints."
            ),
            "schema": (
                "https://schema.getpostman.com/"
                "json/collection/v2.1.0/"
                "collection.json"
            ),
        },
        "item": [],
        "variable": [
            {
                "key": "base_url",
                "value": (
                    "https://msdat-api."
                    "fmohconnect.gov.ng"
                ),
                "type": "string",
            },
            {
                "key": "frontend_token",
                "value": "",
                "type": "string",
            },
            {
                "key": "expired_token",
                "value": "",
                "type": "string",
            },
        ],
    }

    modules = {}

    for functional_file in functional_files:
        generated_data = load_json(
            functional_file
        )

        module_name = generated_data.get(
            "module",
            "Other",
        )

        api_name = generated_data.get(
            "api_name",
            functional_file.stem,
        )

        if module_name not in modules:
            modules[module_name] = {
                "name": module_name,
                "item": [],
            }

        api_folder = {
            "name": api_name,
            "item": [],
        }

        for test_case in generated_data[
            "test_cases"
        ]:
            api_folder["item"].append(
                convert_test_case(
                    test_case
                )
            )

        modules[module_name]["item"].append(
            api_folder
        )

    collection["item"] = list(
        modules.values()
    )

    save_json(
        COLLECTION_OUTPUT,
        collection,
    )

    print(
        "Postman collection created successfully:"
    )
    print(COLLECTION_OUTPUT)


if __name__ == "__main__":
    build_collection()
