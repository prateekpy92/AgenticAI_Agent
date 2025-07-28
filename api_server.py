from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
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
    description="API for PDF Question Answering with Ollama and TF-IDF Embeddings",
    version="2.0.0"
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
    status: str

class DocumentInfo(BaseModel):
    filename: str
    status: str
    processing_time: str
    chunks_created: int

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "PDF Q&A API is running",
        "version": "2.0.0",
        "features": [
            "PDF document processing",
            "Local Ollama integration",
            "TF-IDF embeddings (no PyTorch dependencies)",
            "Search history management",
            "RESTful API interface"
        ],
        "endpoints": {
            "upload": "/upload-pdf/",
            "query": "/ask-question/",
            "history": "/history/",
            "status": "/status/"
        }
    }

@app.post("/upload-pdf/", response_model=dict)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Check file size (limit to 10MB)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum 10MB allowed."
        )
    
    start_time = datetime.now()
    
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
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if success:
            doc_info = pdf_processor.get_document_info()
            return {
                "message": f"PDF '{file.filename}' processed successfully",
                "filename": file.filename,
                "status": "success",
                "processing_time": f"{processing_time:.2f} seconds",
                "document_info": doc_info
            }
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
    
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )
    
    try:
        start_time = datetime.now()
        answer = pdf_processor.ask_question(request.question)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if answer indicates an error
        if answer.startswith("Error"):
            status = "error"
        else:
            status = "success"
            # Save to history only if successful
            history_manager.add_entry(
                question=request.question,
                answer=answer,
                filename=pdf_processor.get_current_file()
            )
        
        return QuestionResponse(
            answer=answer,
            filename=pdf_processor.get_current_file(),
            timestamp=timestamp,
            status=status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )

@app.get("/history/")
async def get_history():
    """Get search history with statistics"""
    try:
        history = history_manager.get_history()
        stats = history_manager.get_statistics()
        
        return {
            "history": history,
            "statistics": stats,
            "total_entries": len(history)
        }
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
        return {"message": "Search history cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing history: {str(e)}"
        )

@app.get("/status/")
async def get_status():
    """Get comprehensive API status"""
    doc_info = pdf_processor.get_document_info()
    stats = history_manager.get_statistics()
    
    return {
        "api_status": "running",
        "version": "2.0.0",
        "pdf_processor": {
            "ready": pdf_processor.is_ready(),
            "current_file": pdf_processor.get_current_file(),
            "document_info": doc_info
        },
        "history": {
            "total_queries": stats["total_queries"],
            "unique_files": stats["unique_files"],
            "most_recent": stats["most_recent"]
        },
        "system": {
            "embedding_type": "TF-IDF",
            "model": "Ollama (Local)",
            "dependencies": "No PyTorch required"
        }
    }

@app.get("/export-history/")
async def export_history():
    """Export history to CSV file"""
    try:
        filename = history_manager.export_to_csv()
        return FileResponse(
            filename,
            media_type="text/csv",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting history: {str(e)}"
        )

# Health check endpoint
@app.get("/health/")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Run server
if __name__ == "__main__":
    print("🚀 Starting PDF Q&A API server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Interactive API: http://localhost:8000/redoc")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
