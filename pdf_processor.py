import os
import warnings
warnings.filterwarnings('ignore')

# Force CPU usage and set environment variables BEFORE any other imports
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCH_USE_CUDA_DSA'] = '0'
os.environ['OMP_NUM_THREADS'] = '1'

from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import Ollama
import streamlit as st

# Custom embedding class to handle PyTorch compatibility issues
class SafeHuggingFaceEmbeddings:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.client = None
        self._initialize_model()
    
    def _initialize_model(self):
        try:
            import sentence_transformers
            import torch
            
            # Try different initialization methods
            initialization_methods = [
                lambda: sentence_transformers.SentenceTransformer(
                    self.model_name, 
                    device='cpu',
                    cache_folder=None
                ),
                lambda: sentence_transformers.SentenceTransformer(
                    self.model_name,
                    device='cpu'
                )
            ]
            
            for i, method in enumerate(initialization_methods):
                try:
                    self.client = method()
                    print(f"✅ Successfully initialized embeddings with method {i+1}")
                    break
                except Exception as e:
                    print(f"⚠️ Initialization method {i+1} failed: {str(e)}")
                    continue
            
            if self.client is None:
                # Final fallback - try with langchain embeddings
                from langchain.embeddings import HuggingFaceEmbeddings
                fallback_embeddings = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'device': 'cpu'}
                )
                self.client = fallback_embeddings.client
                print("✅ Fallback embeddings initialized")
                
        except Exception as e:
            st.error(f"❌ Failed to initialize embeddings: {str(e)}")
            st.error("Please run: pip install torch==1.13.1 sentence-transformers==2.2.2 --force-reinstall")
            raise e
    
    def embed_documents(self, texts):
        if self.client is None:
            raise Exception("Model not initialized")
        return [self.client.encode(text).tolist() for text in texts]
    
    def embed_query(self, text):
        if self.client is None:
            raise Exception("Model not initialized")
        return self.client.encode(text).tolist()

class PDFProcessor:
    def __init__(self):
        self.vectordb = None
        self.qa_chain = None
        self.current_file = None
        self.embeddings = None
        
    def process_pdf(self, file_path: str, filename: str) -> bool:
        """Process a PDF file and create the QA chain"""
        try:
            # Load PDF
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                return False
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100
            )
            chunks = text_splitter.split_documents(documents)
            
            if not chunks:
                return False
            
            # Initialize embeddings if not already done
            if self.embeddings is None:
                try:
                    self.embeddings = SafeHuggingFaceEmbeddings()
                except Exception as e:
                    st.error(f"Error initializing embeddings: {str(e)}")
                    return False
            
            # Create vector store
            self.vectordb = FAISS.from_documents(chunks, self.embeddings)
            
            # Initialize Ollama LLM
            llm = Ollama(
                model="llama2",  # Change to your preferred model
                base_url="http://localhost:11434"
            )
            
            # Create QA chain
            retriever = self.vectordb.as_retriever(search_kwargs={"k": 3})
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=False
            )
            
            self.current_file = filename
            return True
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return False
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the processed PDF"""
        if not self.qa_chain:
            return "No PDF processed. Please upload and process a PDF first."
        
        try:
            response = self.qa_chain.run(question)
            return response
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def is_ready(self) -> bool:
        """Check if PDF is processed and ready for questions"""
        return self.qa_chain is not None
    
    def get_current_file(self) -> str:
        """Get the current processed file name"""
        return self.current_file or "No file processed"
