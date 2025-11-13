from fastapi import APIRouter, UploadFile, File, HTTPException
from agent.setup.chroma_db.pdf_processor import FAQProcessor
import os
import shutil

router = APIRouter()
faq_processor = None

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_faq_processor():
    """Lazy initialization of FAQ processor."""
    global faq_processor
    if faq_processor is None:
        faq_processor = FAQProcessor()
    return faq_processor


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process FAQ PDF file.
    
    The file will be chunked and stored in ChromaDB.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the PDF
        processor = get_faq_processor()
        result = await processor.process_pdf(file_path, file.filename)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
