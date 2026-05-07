from fastapi import FastAPI, UploadFile, File
import pandas as pd
import io
import os
from pypdf import PdfReader
from datetime import datetime

app = FastAPI()

# Ensure the 'data' folder exists
if not os.path.exists("data"):
    os.makedirs("data")

@app.post("/audit")
async def do_audit(reg_pdf: UploadFile = File(...), telemetry_csv: UploadFile = File(...)):
    """
    RCaaS Agentic Auditor: 
    Matches unstructured regulatory PDFs with structured telemetry.
    Saves a record of every audit in the /data folder.
    """
    
    # --- 1. SAVE FOR THE AUDIT TRAIL ---
    # We save the files with a timestamp so you have a history of every audit
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = f"data/{timestamp}_{reg_pdf.filename}"
    csv_path = f"data/{timestamp}_{telemetry_csv.filename}"

    # Read contents once to process and save
    pdf_bytes = await reg_pdf.read()
    csv_bytes = await telemetry_csv.read()

    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    with open(csv_path, "wb") as f:
        f.write(csv_bytes)

    # --- 2. THE INGESTION LAYER (PDF) ---
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = reader.pages[0].extract_text()
    threshold = 15.0 if "15" in text else 10.0

    # --- 3. THE DATA LAYER (CSV) ---
    df = pd.read_csv(io.BytesIO(csv_bytes))
    
    # --- 4. THE REASONING ENGINE ---
    results = []
    for index, row in df.iterrows():
        val = row['biomass_density']
        status = "PASS" if val >= threshold else "FAIL"
        results.append({
            "point": index,
            "measured": val,
            "status": status
        })
    
    return {
        "audit_id": f"RCaaS-{timestamp}", 
        "storage_location": "data/",
        "compliance_summary": {
            "total_checked": len(results),
            "pass_count": sum(1 for r in results if r["status"] == "PASS")
        },
        "detailed_ledger": results,
        "verification_statement": f"Audit complete. Evidence stored as {pdf_path} and {csv_path}"
    }