import os
from pathlib import Path

from utils.vector_db import VectorDBManager
from utils.config import Config


def create_dbs():
    # Use BASE_DIR/data so it works no matter where you run from
    data_dir = Config.BASE_DIR / "data"
    if not data_dir.exists():
        print(f"Data directory not found at {data_dir}!")
        return

    # Map filenames to company names
    file_mapping = {
        "GOOG-10-Q-Q3-2025.pdf": "Google",
        "MSFT_FY26Q1_10Q.pdf": "Microsoft",
        "adbe-10q-q325-final.pdf": "Adobe",
        "cisco.pdf": "Cisco",
        "cognizant.pdf": "Cognizant",
        "juniper.pdf": "Juniper",
        "salesforce.pdf": "Salesforce",
        "wipro.pdf": "Wipro",
        "alphabet.pdf": "Alphabet",
    }

    db_manager = VectorDBManager()

    for filename, company_name in file_mapping.items():
        pdf_path = data_dir / filename
        if pdf_path.exists():
            print(f"Processing {company_name} ({filename})...")
            try:
                db_manager.create_vector_db(company_name, str(pdf_path))
                print(f"Successfully created DB for {company_name}")
            except Exception as e:
                print(f"Error creating DB for {company_name}: {e}")
        else:
            print(f"File not found: {pdf_path}")

if __name__ == "__main__":
    create_dbs()
