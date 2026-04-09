import os
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel

from app.services.document_ai import DocumentExtractor, ExtractedBill
from app.services.policy_nlp import PolicyParser, PolicyRule
from app.services.rule_engine import RuleEngine, ClaimResult
from app.services.explainer import Explainer
from app.db.database import save_rule_to_pg, save_claim_to_mongo, get_all_claims
from app import auth

app = FastAPI(title="Explainable Claim Adjudication API", version="1.0")

app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local research purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize singletons for services to load models once into memory
extractor = DocumentExtractor()
parser = PolicyParser()
engine = RuleEngine()

class AdjudicateRequest(BaseModel):
    bill: ExtractedBill
    policy_text: str

@app.get("/")
def read_root():
    return {"status": "Research Engine Online", "models_loaded": True}

@app.post("/api/extract_bill", response_model=ExtractedBill)
async def extract_bill(file: UploadFile = File(...)):
    """
    Endpoint for Hospital interface to upload a raw bill image/pdf.
    """
    # Save file to disk
    os.makedirs("temp_uploads", exist_ok=True)
    file_path = os.path.join("temp_uploads", file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    extracted = extractor.extract_from_image(file_path)
    return extracted

import PyPDF2

@app.post("/api/parse_policy", response_model=List[PolicyRule])
async def parse_policy(policy_text: str = Form(...)):
    """
    Endpoint for Insurance interface to upload policy rules.
    """
    rules = parser.parse_policy_text(policy_text)
    # Persist rules to local SQLite DB
    for rule in rules:
        save_rule_to_pg(rule.dict())
    return rules

@app.post("/api/extract_policy_pdf")
async def extract_policy_pdf(file: UploadFile = File(...)):
    """
    Endpoint for Insurance interface to upload a PDF file containing policy rules.
    """
    os.makedirs("temp_uploads", exist_ok=True)
    file_path = os.path.join("temp_uploads", file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_text = ""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF: {e}")

    # Optionally parse rules immediately, or just return text for frontend to parse later.
    # Our flow: frontend extracts text then calls adjudicate with it. But we can also parse the rules here
    # to save them in SQLite.
    if extracted_text.strip():
        rules = parser.parse_policy_text(extracted_text)
        for rule in rules:
            save_rule_to_pg(rule.dict())

    return {"policy_text": extracted_text}

@app.post("/api/adjudicate")
async def adjudicate_claim(req: AdjudicateRequest):
    """
    End-to-end adjudication for the Patient dashboard using raw JSON bill and string text.
    """
    try:
        rules = parser.parse_policy_text(req.policy_text)
        result = engine.adjudicate(req.bill, rules)
        explanation = Explainer.generate_report(result)
        
        claim_record = {
            "bill": req.bill.dict(),
            "policy_text": req.policy_text,
            "result": result.dict(),
            "explanation": explanation
        }
        # Save historical adjudication
        save_claim_to_mongo(claim_record)
        
        return {
            "result": result.dict(),
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/claims")
async def fetch_claims():
    """
    Endpoint for Insurance dashboard to view historical adjudications.
    """
    claims = get_all_claims()
    return claims

