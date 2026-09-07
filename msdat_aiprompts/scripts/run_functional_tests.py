import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

COLLECTION_FILE = (
    BASE_DIR
    / "postman"
    / "collections"
    / "msdat_functional_tests.postman_collection.json"
)

RESULTS_DIR = BASE_DIR / "outputs" / "functional-results"
RESULT_FILE = RESULTS_DIR / "newman_results.json"


def run_newman():
    if not COLLECTION_FILE.exists():
        raise FileNotFoundError(
            f"Postman collection not found: {COLLECTION_FILE}"
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    command = [
        "newman",
        "run",
        str(COLLECTION_FILE),
        "--reporters",
        "cli,json",
        "--reporter-json-export",
        str(RESULT_FILE),
    ]

    print("Starting Newman functional test execution...")
    print(f"Collection: {COLLECTION_FILE}")
    print(f"Results: {RESULT_FILE}")

    result = subprocess.run(command, check=False)

    print("\nNewman execution completed.")

    if RESULT_FILE.exists():
        print(f"Results saved successfully: {RESULT_FILE}")
    else:
        print("Warning: Newman result file was not created.")

    return result.returncode


def main():
    try:
        exit_code = run_newman()
        sys.exit(exit_code)

    except Exception as error:
        print(f"Functional test execution failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
