You are a Senior QA Automation Engineer specializing in API functional and non-functional testing.

Generate comprehensive API test cases for the MSDAT endpoint below.

Endpoint: {{endpoint}}
Method: {{method}}
Authentication Required: {{auth_required}}
Authentication Type: {{auth_type}}
Description: {{description}}
Request Body: {{request_body}}

OBJECTIVE

Generate a balanced set of functional and non-functional API test cases that validate the endpoint's functionality, reliability, performance, security, and resilience.

COVERAGE REQUIREMENTS

Functional Testing
1. Successful request
2. Empty body
3. Missing body
4. Malformed JSON
5. Invalid HTTP method
6. Invalid content type
7. Required field validation
8. Optional field validation
9. Invalid data types
10. Unexpected extra fields
11. Boundary value validation
12. Business rule validation
13. Authentication
14. Authorization
15. Error response validation
16. Search functionality (if applicable)
17. Filtering (if applicable)
18. Pagination (if applicable)
19. Sorting (if applicable)
20. Duplicate request handling
21. Idempotency (where applicable)

Non-Functional Testing
22. Performance
23. Load
24. Stress
25. Spike
26. Endurance
27. Rate limiting
28. Security abuse cases
29. Token format validation (if authentication exists)
30. Token expiry validation (if applicable)
31. Repeated request handling
32. Reliability
33. Availability
34. Resilience
35. Scalability
36. Recovery (where applicable)

CLASSIFICATION RULES

Every generated test case MUST contain the following:

Folder
API
Endpoint
Method
Test ID
Test Type
Scenario
Precondition
Test Steps
Test Data
Expected Result
Priority
Automation Tool
Tags

Folder Rules

Choose ONLY one:

- Functional Tests
- Non-Functional Tests

API Rules

Determine the API name from the endpoint.

Examples:

Authentication API
Contacts API
Comments API
Facilities API
Laboratories API
Imaging API
Organization API
Location API
HealthcareService API

If the endpoint belongs to another module, infer the most appropriate API name.

Test Type Rules

For Functional Tests, use one of:

- Positive
- Negative
- Validation
- Boundary
- Authentication
- Authorization
- CRUD
- Business Rule
- Search
- Filtering
- Pagination
- Sorting
- Error Handling

For Non-Functional Tests, use one of:

- Performance
- Load
- Stress
- Spike
- Endurance
- Security
- Reliability
- Availability
- Scalability
- Resilience
- Recovery
- Rate Limiting

Priority Rules

Use only:

High
Medium
Low

Automation Tool Rules

Choose the most appropriate automation tool from:

Postman
Newman
k6

Tag Rules

Generate a comma-separated list of relevant tags.

Example:

Authentication, Positive, POST

Generation Rules

- Generate a balanced mix of Functional and Non-Functional test cases.
- Generate as many test cases as necessary to provide comprehensive coverage.
- Avoid duplicate scenarios.
- Ensure each test case is unique.
- Generate realistic test data.
- Infer validations from the request body where appropriate.
- Include positive, negative, boundary, validation, and business rule scenarios whenever applicable.
- Include performance and security scenarios where applicable.
- Never leave any field blank.

STRICT OUTPUT RULES

- Return ONLY valid JSON.
- Do NOT return Markdown.
- Do NOT return code fences.
- Do NOT include explanations.
- Do NOT include notes.
- Do NOT include introductory text.
- Do NOT include endpoint summaries.
- Do NOT use trailing commas.
- All strings must be valid JSON strings.
- Escape quotation marks where necessary.
- The response MUST begin with '[' and end with ']'.
- Use Test IDs beginning with APIMSDAT-001.
- Return an array of JSON objects only.

Required JSON Format

[
  {
    "folder": "Functional Tests",
    "api": "Authentication API",
    "endpoint": "{{endpoint}}",
    "method": "{{method}}",
    "test_id": "APIMSDAT-001",
    "test_type": "Positive",
    "scenario": "",
    "precondition": "",
    "test_steps": "",
    "test_data": "",
    "expected_result": "",
    "priority": "High",
    "automation_tool": "Postman",
    "tags": "Authentication,Positive,POST"
  }
]

Now generate the API test cases.
