import json
from pathlib import Path
from urllib.parse import urlencode


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
    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    return json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
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
    if not isinstance(headers, dict):
        return []

    return [
        {
            "key": str(key),
            "value": (
                ""
                if value is None
                else str(value)
            ),
            "type": "text",
        }
        for key, value in headers.items()
    ]


def convert_query_parameters(
    query_parameters,
):
    if not isinstance(
        query_parameters,
        dict,
    ):
        return []

    return [
        {
            "key": str(key),
            "value": (
                ""
                if value is None
                else str(value)
            ),
        }
        for key, value
        in query_parameters.items()
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
                    "language": "json",
                }
            },
        }

    if body_mode == "urlencoded":
        if not isinstance(
            request_body,
            dict,
        ):
            request_body = {}

        return {
            "mode": "urlencoded",
            "urlencoded": [
                {
                    "key": str(key),
                    "value": (
                        ""
                        if value is None
                        else str(value)
                    ),
                    "type": "text",
                }
                for key, value
                in request_body.items()
            ],
        }

    if body_mode == "formdata":
        if not isinstance(
            request_body,
            dict,
        ):
            request_body = {}

        return {
            "mode": "formdata",
            "formdata": [
                {
                    "key": str(key),
                    "value": (
                        ""
                        if value is None
                        else str(value)
                    ),
                    "type": "text",
                }
                for key, value
                in request_body.items()
            ],
        }

    return None


def build_url(request_data):
    raw_url = request_data["url"]

    query_parameters = request_data.get(
        "query_parameters",
        {},
    )

    if (
        query_parameters
        and "?" not in raw_url
    ):
        query_string = urlencode(
            query_parameters,
            doseq=True,
        )

        raw_url = (
            f"{raw_url}?{query_string}"
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


def should_save_frontend_token(
    test_case,
):
    request_data = test_case.get(
        "request",
        {},
    )

    request_url = request_data.get(
        "url",
        "",
    )

    request_method = request_data.get(
        "method",
        "",
    ).upper()

    expected_status = test_case.get(
        "expected_status"
    )

    category = test_case.get(
        "category",
        "",
    )

    return (
        request_url.endswith(
            "/api/auth/frontend-token"
        )
        and request_method == "POST"
        and expected_status == 200
        and category == "Happy Path"
    )


def build_assertion_event(
    assertions,
    save_frontend_token=False,
):
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

    if save_frontend_token:
        assertion_scripts.extend(
            [
                "",
                (
                    "const tokenResponse = "
                    "pm.response.json();"
                ),
                "if (tokenResponse.token) {",
                (
                    "    pm.collectionVariables"
                    ".set("
                ),
                (
                    '        "frontend_token",'
                ),
                (
                    "        "
                    "tokenResponse.token"
                ),
                "    );",
                "}",
            ]
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
            "method": request_data[
                "method"
            ],
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
                test_case["assertions"],
                save_frontend_token=(
                    should_save_frontend_token(
                        test_case
                    )
                ),
            )
        ],
    }

    request_body = build_request_body(
        request_data
    )

    if request_body is not None:
        postman_request[
            "request"
        ]["body"] = request_body

    description = test_case.get(
        "description"
    )

    if description:
        postman_request[
            "request"
        ]["description"] = description

    return postman_request


def module_sort_key(module):
    module_priority = {
        "Authentication API": 0,
    }

    return (
        module_priority.get(
            module["name"],
            1,
        ),
        module["name"],
    )


def api_sort_key(api_folder):
    api_priority = {
        "Generate Frontend Token": 0,
    }

    return (
        api_priority.get(
            api_folder["name"],
            1,
        ),
        api_folder["name"],
    )


def build_collection():
    if not FUNCTIONAL_TESTS_DIR.exists():
        raise FileNotFoundError(
            "Functional test output folder "
            "does not exist: "
            f"{FUNCTIONAL_TESTS_DIR}"
        )

    functional_files = sorted(
        FUNCTIONAL_TESTS_DIR.glob(
            "*.json"
        )
    )

    if not functional_files:
        raise FileNotFoundError(
            "No functional test JSON files "
            "found in "
            f"{FUNCTIONAL_TESTS_DIR}"
        )

    collection = {
        "info": {
            "name": (
                "MSDAT AI Functional Tests"
            ),
            "description": (
                "AI-generated functional API "
                "tests for MSDAT endpoints."
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

        test_cases = generated_data.get(
            "test_cases",
            [],
        )

        if not test_cases:
            print(
                "Skipping file with no "
                "test cases: "
                f"{functional_file}"
            )
            continue

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

        for test_case in test_cases:
            api_folder["item"].append(
                convert_test_case(
                    test_case
                )
            )

        modules[module_name][
            "item"
        ].append(api_folder)

    if not modules:
        raise ValueError(
            "No valid functional test cases "
            "were available to build the "
            "Postman collection."
        )

    for module in modules.values():
        module["item"] = sorted(
            module["item"],
            key=api_sort_key,
        )

    collection["item"] = sorted(
        modules.values(),
        key=module_sort_key,
    )

    save_json(
        COLLECTION_OUTPUT,
        collection,
    )

    total_requests = sum(
        len(api_folder["item"])
        for module
        in collection["item"]
        for api_folder
        in module["item"]
    )

    print(
        "Postman collection created "
        "successfully:"
    )
    print(COLLECTION_OUTPUT)
    print(
        f"Total requests: {total_requests}"
    )
    print(
        "Authentication tests will run "
        "before protected API tests."
    )


if __name__ == "__main__":
    build_collection()
