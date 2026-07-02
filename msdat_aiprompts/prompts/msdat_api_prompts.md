You are a senior QA automation engineer.

Generate security-focused API test cases for the MSDAT authentication endpoint below.

Endpoint: {{endpoint}}
Method: {{method}}
Authentication Required: {{auth_required}}
Authentication Type: {{auth_type}}
Description: {{description}}
Request Body: {{request_body}}

Important Context:
- This endpoint is used to generate the X-Frontend-JWT token.
- No existing token is required to call this endpoint.
- The request body is an empty JSON object: {}.

Generate test cases covering:
1. Successful token generation
2. Empty JSON body {}
3. Missing request body
4. Invalid HTTP method
5. Invalid content type
6. Malformed JSON body
7. Extra unexpected fields
8. Repeated token generation
9. Token format validation
10. Token expiry validation
11. Token usage on protected endpoints
12. Missing token on protected endpoints
13. Invalid token on protected endpoints

Return the result as a markdown table with:
Test ID, Scenario, Precondition, Test Steps, Test Data, Expected Result, Priority, Automation Tool.
