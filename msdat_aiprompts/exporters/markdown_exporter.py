import json
import pandas as pd


def export_markdown(json_text, output_file):

    data = json.loads(json_text)

    df = pd.DataFrame(data)

    markdown = df.to_markdown(index=False)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)
