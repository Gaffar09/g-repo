You are a senior QA automation engineer.

Generate security-focused API test cases for the MSDAT endpoint below.

Endpoint: {{endpoint}}
Method: {{method}}
Authentication Required: {{auth_required}}
Authentication Type: {{auth_type}}
Description: {{description}}
Request Body: {{request_body}}

Coverage Required:
1. Successful request
2. Empty body
3. Missing body
4. Malformed JSON
5. Invalid HTTP method
6. Invalid content type
7. Unexpected extra fields
8. Token format validation, if token is returned
9. Token expiry validation, if applicable
10. Unauthorized access
11. Invalid token
12. Missing token
13. Repeated request handling
14. Error response validation
15. Security abuse cases

STRICT OUTPUT RULES:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include ```json code fences.
- Do not include any introduction.
- Do not include endpoint summary text.
- Do not include notes before or after the JSON.
- Do not use markdown tables.
- Do not use trailing commas.
- All string values must be valid JSON strings.
- Escape all quotes inside values.
- The response must start with [ and end with ].
- Generate at least 5 test cases.
- Use Test IDs starting from APIMSDAT-001.
- Priority must be one of: High, Medium, Low.
- Automation Tool must be one of: Postman, Newman, k6.

Required JSON format:
[
  {
    "test_id": "APIMSDAT-001",
    "scenario": "",
    "precondition": "",
    "test_steps": "",
    "test_data": "",
    "expected_result": "",
    "priority": "High",
    "automation_tool": "Postman"
  }
]

Now generate the API test cases.
