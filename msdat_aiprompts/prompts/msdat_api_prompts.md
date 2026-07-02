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
- Return ONLY one markdown table.
- Do not include any introduction.
- Do not include endpoint summary text.
- Do not include notes before or after the table.
- Do not include bullet points.
- Do not include headings.
- Generate at least 5 test cases.
- Each row must be concise but detailed enough for automation.
- Use Test IDs starting from APIMSDAT-001.
- Automation Tool must be one of: Postman, Newman, k6.

Required table columns:
| Test ID | Scenario | Precondition | Test Steps | Test Data | Expected Result | Priority | Automation Tool |

Now generate the API test cases.
