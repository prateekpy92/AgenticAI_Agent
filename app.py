import streamlit as st
import tempfile
import os
from datetime import datetime
from pdf_processor import PDFProcessor
from history import HistoryManager

# Initialize components
pdf_processor = PDFProcessor()
history_manager = HistoryManager()

# Page configuration
st.set_page_config(
    page_title="PDF Q&A Assistant",
    page_icon="📄",
    layout="wide"
)

# Main title
st.title("📄 PDF Q&A Assistant")
st.write("Upload a PDF document and ask questions about its content using local AI")

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF document to analyze"
    )
    
    if uploaded_file:
        st.success(f"✅ File loaded: {uploaded_file.name}")
        
        # Process the PDF
        if st.button("🔄 Process PDF", type="primary"):
            with st.spinner("Processing PDF..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name
                    
                    # Process the PDF
                    success = pdf_processor.process_pdf(tmp_path, uploaded_file.name)
                    
                    # Cleanup
                    os.unlink(tmp_path)
                    
                    if success:
                        st.success("PDF processed successfully!")
                        st.session_state.pdf_processed = True
                        st.session_state.current_file = uploaded_file.name
                    else:
                        st.error("Failed to process PDF")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Ask Questions")
    
    if not hasattr(st.session_state, 'pdf_processed') or not st.session_state.pdf_processed:
        st.info("👆 Please upload and process a PDF file first")
    else:
        st.info(f"📄 Current document: {st.session_state.current_file}")
        
        # Question input
        question = st.text_input(
            "What would you like to know about the document?",
            placeholder="e.g., What are the main topics discussed?"
        )
        
        if st.button("🔍 Ask Question", type="primary") and question:
            with st.spinner("Generating answer..."):
                try:
                    answer = pdf_processor.ask_question(question)
                    
                    if answer:
                        # Display answer
                        st.subheader("📝 Answer")
                        st.markdown(answer)
                        
                        # Save to history
                        history_manager.add_entry(
                            question=question,
                            answer=answer,
                            filename=st.session_state.current_file
                        )
                        
                        st.success("Answer generated successfully!")
                    else:
                        st.error("Could not generate an answer")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with col2:
    st.header("📊 Search History")
    
    # History controls
    col_refresh, col_clear = st.columns(2)
    with col_refresh:
        if st.button("🔄 Refresh"):
            st.rerun()
    with col_clear:
        if st.button("🗑️ Clear History"):
            history_manager.clear_history()
            st.success("History cleared!")
            st.rerun()
    
    # Display history
    history = history_manager.get_history()
    
    if history:
        st.write(f"**Total queries:** {len(history)}")
        
        for i, entry in enumerate(reversed(history[-10:])):  # Show last 10
            with st.expander(f"Q{len(history)-i}: {entry['question'][:30]}..."):
                st.write(f"**File:** {entry['filename']}")
                st.write(f"**Question:** {entry['question']}")
                st.write(f"**Answer:** {entry['answer']}")
                st.write(f"**Time:** {entry['timestamp']}")
    else:
        st.info("No search history yet")

# Footer
st.divider()
st.caption("Powered by Ollama + Streamlit")
