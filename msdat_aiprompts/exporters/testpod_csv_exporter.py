import json
import pandas as pd


def export_testpod_csv(json_text, output_file):
    data = json.loads(json_text)

    rows = []

    for item in data:
        rows.append({
            "Name": item.get("scenario", ""),
            "ID": item.get("test_id", ""),
            "State": "draft",
            "Priority": item.get("priority", "").lower(),
            "Automation status": "not automated",
            "Type": "functional",
            "Steps": item.get("test_steps", ""),
            "Description": item.get("scenario", ""),
            "Precondition": item.get("precondition", ""),
            "Expected result": item.get("expected_result", "")
        })

    df = pd.DataFrame(rows)

    df = df[
        [
            "Name",
            "ID",
            "State",
            "Priority",
            "Automation status",
            "Type",
            "Steps",
            "Description",
            "Precondition",
            "Expected result"
        ]
    ]

    df.to_csv(output_file, index=False)
