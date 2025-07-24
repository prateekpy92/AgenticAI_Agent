from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import os
from datetime import datetime
from pdf_processor import PDFProcessor
from history import HistoryManager
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="PDF Q&A API",
    description="API for PDF Question Answering with Ollama",
    version="1.0.0"
)

# Initialize components
pdf_processor = PDFProcessor()
history_manager = HistoryManager()

# Pydantic models
class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    filename: str
    timestamp: str

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PDF Q&A API is running", "version": "1.0.0"}

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process the PDF
        success = pdf_processor.process_pdf(tmp_path, file.filename)
        
        # Cleanup temporary file
        os.unlink(tmp_path)
        
        if success:
            return JSONResponse({
                "message": f"PDF '{file.filename}' processed successfully",
                "filename": file.filename,
                "status": "success"
            })
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to process PDF file"
            )
            
    except Exception as e:
        # Ensure cleanup
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/ask-question/", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the processed PDF"""
    
    if not pdf_processor.is_ready():
        raise HTTPException(
            status_code=400,
            detail="No PDF processed. Upload a PDF file first."
        )
    
    try:
        answer = pdf_processor.ask_question(request.question)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to history
        history_manager.add_entry(
            question=request.question,
            answer=answer,
            filename=pdf_processor.get_current_file()
        )
        
        return QuestionResponse(
            answer=answer,
            filename=pdf_processor.get_current_file(),
            timestamp=timestamp
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )

@app.get("/history/")
async def get_history():
    """Get search history"""
    try:
        history = history_manager.get_history()
        return JSONResponse(history)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving history: {str(e)}"
        )

@app.delete("/history/")
async def clear_history():
    """Clear search history"""
    try:
        history_manager.clear_history()
        return JSONResponse({"message": "Search history cleared successfully"})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing history: {str(e)}"
        )

@app.get("/status/")
async def get_status():
    """Get API status and current file info"""
    return JSONResponse({
        "status": "running",
        "pdf_ready": pdf_processor.is_ready(),
        "current_file": pdf_processor.get_current_file(),
        "history_count": len(history_manager.get_history())
    })

# Run server
if __name__ == "__main__":
    print("🚀 Starting PDF Q&A API server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
