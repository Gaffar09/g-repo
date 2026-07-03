import json
import pandas as pd


def export_csv(json_text, output_file):
    data = json.loads(json_text)

    df = pd.DataFrame(data)

    df.to_csv(output_file, index=False)
