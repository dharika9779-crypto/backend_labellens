from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os


from pdf_report import generate_pdf_report
from fastapi.responses import Response
from ocr import extract_text_from_image
from barcode import process_barcode_image, fetch_product_from_barcode
from processing import clean_and_extract, clean_and_extract_nlp
from classifier import full_analysis, full_analysis_with_enumbers
from personalization import personalise

app = FastAPI(title="AI Ingredient Transparency System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FullScanRequest(BaseModel):
    raw_text: str
    is_diabetic: bool = False
    allergies: list[str] = []
    age: str = "adult"
    diet_type: str = "none"
    medical_conditions: list[str] = []

@app.get("/")
def root():
    return {"message": "Backend is running!"}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type")
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    result = extract_text_from_image(image_bytes, file.filename or "upload.jpg")
    return JSONResponse(content=result)

@app.post("/full-scan")
def full_scan(body: FullScanRequest):
    if not body.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text empty")

    processing_result = clean_and_extract_nlp(body.raw_text)

    analysis = full_analysis_with_enumbers(
        processing_result["ingredients_list"],
        processing_result.get("e_numbers", [])
    )

    personal_result = personalise(
        classified=analysis["classified"],
        health_score=analysis["health_score"],
        is_diabetic=body.is_diabetic,
        user_allergies=body.allergies,
    )

    return JSONResponse(content={
        "ingredients_raw_block": processing_result["ingredients_raw_block"],
        "ingredients_list": processing_result["ingredients_list"],
        "nlp_used": processing_result.get("nlp_used", False),
        "corrections_made": processing_result.get("corrections_made", False),
        "e_numbers": processing_result.get("e_numbers", []),
        **analysis,
        "personalisation": personal_result,
    })


# ── BARCODE IMAGE UPLOAD ──────────────────────────────────────
@app.post("/scan-barcode")
async def scan_barcode(file: UploadFile = File(...)):
    """
    Barcode image upload karo → product ingredients fetch karo
    """
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    result = process_barcode_image(image_bytes)
    return JSONResponse(content=result)


# ── BARCODE NUMBER DIRECT ─────────────────────────────────────
class BarcodeRequest(BaseModel):
    barcode: str

@app.post("/lookup-barcode")
def lookup_barcode(body: BarcodeRequest):
    """
    Seedha barcode number do → product info lo
    """
    if not body.barcode.strip():
        raise HTTPException(status_code=400, detail="Barcode empty")
    
    result = fetch_product_from_barcode(body.barcode.strip())
    return JSONResponse(content=result)

# ── PDF REPORT ────────────────────────────────────────────────
class PDFReportRequest(BaseModel):
    product_name: str = "Unknown Product"
    ingredients_list: list[str] = []
    classified: list[dict] = []
    counts: dict = {}
    health_score: dict = {}
    personalisation: dict = {}
    user_name: str = ""

@app.post("/generate-pdf")
def generate_pdf(body: PDFReportRequest):
    """
    Analysis data lo → professional PDF report banao → return karo
    """
    pdf_bytes = generate_pdf_report(
        product_name=body.product_name,
        ingredients_list=body.ingredients_list,
        classified=body.classified,
        counts=body.counts,
        health_score=body.health_score,
        personalisation=body.personalisation,
        user_name=body.user_name,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=labellens-report.pdf"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)