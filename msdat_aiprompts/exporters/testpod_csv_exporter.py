import json
import pandas as pd


def export_testpod_csv(json_text, output_file):
    data = json.loads(json_text)

    rows = []

    for item in data:
        rows.append({
            "Test Case ID": item.get("test_id", ""),
            "Title": item.get("scenario", ""),
            "Description": item.get("scenario", ""),
            "Precondition": item.get("precondition", ""),
            "Steps": item.get("test_steps", ""),
            "Test Data": item.get("test_data", ""),
            "Expected Result": item.get("expected_result", ""),
            "Priority": item.get("priority", ""),
            "Test Type": "API",
            "Automation Tool": item.get("automation_tool", ""),
            "Automation Status": "Not Automated"
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
