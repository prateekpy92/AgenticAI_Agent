import os
import warnings
warnings.filterwarnings('ignore')

from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import Ollama
import streamlit as st
from typing import List, Tuple
import re

class ImprovedTextProcessor:
    def __init__(self):
        self.documents = []
        self.doc_vectors = []
        
    def preprocess_text(self, text: str) -> List[str]:
        """Enhanced text preprocessing"""
        # Convert to lowercase and extract words
        text = text.lower()
        # Include numbers and handle hyphenated words better
        words = re.findall(r'\b\w+(?:-\w+)*\b', text)
        
        # Minimal stop words to preserve more context
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        return [word for word in words if word not in stop_words and len(word) > 1]
    
    def calculate_similarity(self, query_words: List[str], doc_words: List[str]) -> float:
        """Improved similarity calculation with fuzzy matching"""
        if not query_words or not doc_words:
            return 0.0
        
        query_set = set(query_words)
        doc_set = set(doc_words)
        
        # Direct word overlap
        direct_overlap = len(query_set.intersection(doc_set))
        
        # Fuzzy matching for partial words
        fuzzy_matches = 0
        for q_word in query_words:
            for d_word in doc_words:
                # Check if words contain each other (substring matching)
                if len(q_word) > 3 and len(d_word) > 3:
                    if q_word in d_word or d_word in q_word:
                        fuzzy_matches += 0.7
                        break
                # Check for similar beginnings
                elif len(q_word) > 2 and len(d_word) > 2:
                    if q_word[:3] == d_word[:3]:
                        fuzzy_matches += 0.5
                        break
        
        # Calculate combined score
        total_matches = direct_overlap + fuzzy_matches
        max_possible = max(len(query_words), len(doc_words))
        
        similarity = total_matches / max_possible if max_possible > 0 else 0.0
        
        return min(similarity, 1.0)  # Cap at 1.0
    
    def add_documents(self, docs: List[str]):
        """Add documents to the processor"""
        self.documents = docs
        self.doc_vectors = [self.preprocess_text(doc) for doc in docs]
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Enhanced search with better ranking"""
        query_words = self.preprocess_text(query)
        
        if not query_words:
            return []
        
        similarities = []
        for i, doc_words in enumerate(self.doc_vectors):
            similarity = self.calculate_similarity(query_words, doc_words)
            
            # Boost score if document contains key terms
            key_terms_bonus = 0
            doc_lower = self.documents[i].lower()
            query_lower = query.lower()
            
            # Check for exact phrase matches
            if any(term in doc_lower for term in query_lower.split() if len(term) > 2):
                key_terms_bonus += 0.2
            
            # Check for important compound terms
            compound_terms = re.findall(r'\b\w+[-\s]\w+\b', query_lower)
            for compound in compound_terms:
                if compound.replace('-', ' ') in doc_lower or compound.replace(' ', '-') in doc_lower:
                    key_terms_bonus += 0.3
            
            final_score = similarity + key_terms_bonus
            similarities.append((i, final_score))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in similarities[:k]:
            if score > 0:  # Include any non-zero similarity
                results.append((self.documents[idx], score))
        
        return results

class PDFProcessor:
    def __init__(self):
        self.text_processor = None
        self.llm = None
        self.current_file = None
        self.chunks = []
        
    def process_pdf(self, file_path: str, filename: str) -> bool:
        """Process a PDF file and create the QA system"""
        try:
            # Load PDF
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                return False
            
            # Split documents into smaller chunks for better granularity
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,  # Smaller chunks for better precision
                chunk_overlap=150,  # More overlap for context
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ";", ":", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            
            if not chunks:
                return False
            
            # Store chunks as text
            self.chunks = [chunk.page_content for chunk in chunks]
            
            # Initialize improved text processor
            self.text_processor = ImprovedTextProcessor()
            self.text_processor.add_documents(self.chunks)
            
            # Initialize Ollama LLM
            try:
                self.llm = Ollama(
                    model="llama2",
                    base_url="http://localhost:11434",
                    temperature=0.2  # Slightly higher for more natural responses
                )
                
                # Test connection
                test_response = self.llm.invoke("Hello")
                
            except Exception as ollama_error:
                st.error(f"Could not connect to Ollama: {str(ollama_error)}")
                return False
            
            self.current_file = filename
            return True
            
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            return False
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the processed PDF with improved retrieval"""
        if not self.text_processor or not self.llm:
            return "No PDF processed. Please upload and process a PDF first."
        
        if not question.strip():
            return "Please enter a valid question."
        
        try:
            # Search for relevant document chunks
            relevant_docs = self.text_processor.search(question, k=8)  # Get more chunks
            
            if not relevant_docs:
                return f"I couldn't find any relevant content in the document '{self.current_file}' for your question."
            
            # Debug: Show similarity scores (remove in production)
            max_similarity = max([score for _, score in relevant_docs]) if relevant_docs else 0.0
            
            # Very permissive threshold - try to answer unless completely irrelevant
            if max_similarity < 0.01:
                return f"I cannot find relevant information in the document '{self.current_file}' to answer your question about '{question}'. The document may not contain this information."
            
            # Get the best chunks - take more for better context
            best_chunks = []
            for doc, score in relevant_docs[:5]:  # Top 5 chunks
                if score > 0:
                    best_chunks.append(doc)
            
            if not best_chunks:
                return f"No relevant content found in '{self.current_file}' for your question."
            
            # Combine chunks with clear separation
            context = "\n---\n".join(best_chunks)
            
            # Improved prompt for better extraction
            prompt = f"""You are a helpful assistant that answers questions based on document content. Read the document content below carefully and answer the user's question.

Document Content:
{context}

Question: {question}

Instructions:
- Answer the question using information from the document content above
- If the document contains relevant information, provide a clear and helpful answer
- If the document doesn't contain the specific information needed, say "The document doesn't contain specific information about [topic]"
- Be specific and cite information from the document when possible
- Focus on being helpful and accurate

Answer:"""
            
            # Get response from Ollama
            response = self.llm.invoke(prompt)
            
            # Clean up the response
            response = response.strip()
            
            if len(response) < 5:
                return f"I couldn't generate a proper answer from the document content for your question about '{question}'."
            
            return response
                
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def is_ready(self) -> bool:
        """Check if PDF is processed and ready for questions"""
        return self.text_processor is not None and self.llm is not None
    
    def get_current_file(self) -> str:
        """Get the current processed file name"""
        return self.current_file or "No file processed"
    
    def get_document_info(self) -> dict:
        """Get information about the processed document"""
        if not self.text_processor:
            return {"status": "No document processed"}
        
        return {
            "status": "Ready",
            "filename": self.current_file,
            "chunks": len(self.chunks),
            "embedding_type": "Enhanced Text Similarity",
            "model": "Llama2 (Ollama)"
        }
