import streamlit as st
import tempfile
import os
from datetime import datetime
from pdf_processor import PDFProcessor
from history import HistoryManager
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Initialize components
if 'pdf_processor' not in st.session_state:
    st.session_state.pdf_processor = PDFProcessor()
if 'history_manager' not in st.session_state:
    st.session_state.history_manager = HistoryManager()

# Page configuration
st.set_page_config(
    page_title="PDF Q&A Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom gradient title styling (similar to snowChat)
gradient_text_html = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700;900&display=swap');

.pdf-chat-title {
  font-family: 'Poppins', sans-serif;
  font-weight: 900;
  font-size: 4em;
  background: linear-gradient(90deg, #4285f4, #34a853, #fbbc05, #ea4335);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
  margin: 0;
  padding: 20px 0;
  text-align: center;
}

.subtitle {
  text-align: center;
  color: #666;
  font-size: 1.2em;
  margin-bottom: 30px;
}

/* Chat message styling */
.user-message {
  background-color: #f0f2f6;
  padding: 12px 16px;
  border-radius: 18px;
  margin: 8px 0;
  margin-left: 15%;
  color: #1f1f1f;
  border: 1px solid #e1e5e9;
}

.assistant-message {
  background-color: #ffffff;
  padding: 12px 16px;
  border-radius: 18px;
  margin: 8px 0;
  margin-right: 15%;
  color: #1f1f1f;
  border: 1px solid #e1e5e9;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.system-message {
  background-color: #e8f4f8;
  padding: 10px 16px;
  border-radius: 12px;
  margin: 8px 0;
  color: #1565c0;
  border-left: 4px solid #2196f3;
  font-style: italic;
}

/* Model selection styling */
.stRadio > div {
  flex-direction: row;
  gap: 20px;
}

.stRadio > div > label {
  background-color: #f8f9fa;
  padding: 10px 20px;
  border-radius: 25px;
  border: 2px solid #e9ecef;
  cursor: pointer;
  transition: all 0.3s ease;
}

.stRadio > div > label:hover {
  background-color: #e9ecef;
  border-color: #4285f4;
}

/* Sidebar styling */
.css-1d391kg {
  background-color: #f8f9fa;
}

/* Button styling */
.stButton > button {
  border-radius: 20px;
  border: none;
  background: linear-gradient(45deg, #4285f4, #34a853);
  color: white;
  padding: 8px 24px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

/* File uploader styling */
.stFileUploader > div {
  border: 2px dashed #4285f4;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  background-color: #f8f9ff;
}

/* Input box styling */
.stTextInput > div > div > input {
  border-radius: 25px;
  border: 2px solid #e1e5e9;
  padding: 12px 20px;
  font-size: 16px;
}

.stTextInput > div > div > input:focus {
  border-color: #4285f4;
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
}
</style>
"""

st.markdown(gradient_text_html, unsafe_allow_html=True)

# Main title with gradient
st.markdown('<div class="pdf-chat-title">PDF Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Talk your way through documents</div>', unsafe_allow_html=True)

# Model selection (similar to snowChat)
model_options = {
    "Ollama Llama2": "Llama2 (Local)",
    "Ollama Mistral": "Mistral (Local)", 
    "Ollama CodeLlama": "CodeLlama (Local)",
    "Ollama Gemma": "Gemma (Local)",
}

model = st.radio(
    "Choose your AI Model:",
    options=list(model_options.keys()),
    format_func=lambda x: model_options[x],
    index=0,
    horizontal=True,
)
st.session_state["model"] = model

# Initialize session state variables
if "assistant_response_processed" not in st.session_state:
    st.session_state["assistant_response_processed"] = True

if "toast_shown" not in st.session_state:
    st.session_state["toast_shown"] = False

if "rate-limit" not in st.session_state:
    st.session_state["rate-limit"] = False

# Show toasts and warnings
if not st.session_state["toast_shown"]:
    st.toast("Welcome to PDF Chat! Upload a document to get started.", icon="👋")
    st.session_state["toast_shown"] = True

if st.session_state["rate-limit"]:
    st.toast("Processing... Please wait", icon="⚠️")
    st.session_state["rate-limit"] = False

# Initial welcome messages
INITIAL_MESSAGE = [
    {"role": "user", "content": "Hi!"},
    {
        "role": "assistant", 
        "content": "Hey there! I'm your PDF assistant, ready to help you explore and understand your documents. Upload a PDF and let's dive in! 📄✨",
    },
]

# Sidebar content
with st.sidebar:
    st.markdown("## 📁 Document Manager")
    
    # Current document status
    if st.session_state.pdf_processor.is_ready():
        st.success(f"📄 **Active:** {st.session_state.pdf_processor.get_current_file()}")
        st.info(f"🤖 **Model:** {model_options[model]}")
    else:
        st.info("No document loaded")
        st.info(f"🤖 **Model:** {model_options[model]}")
    
    st.markdown("---")
    
    # File uploader
    st.markdown("### Upload PDF Document")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF document to analyze",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.success(f"✅ **{uploaded_file.name}**")
        st.caption(f"Size: {uploaded_file.size / 1024:.1f} KB")
        
        if st.button("🚀 Process Document", type="primary", use_container_width=True):
            with st.spinner("🔄 Processing document..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name
                    
                    success = st.session_state.pdf_processor.process_pdf(tmp_path, uploaded_file.name)
                    os.unlink(tmp_path)
                    
                    if success:
                        st.success("✅ Document processed!")
                        st.balloons()
                        # Add system message
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"📄 Document '{uploaded_file.name}' has been processed and is ready for questions."
                        })
                        st.rerun()
                    else:
                        st.error("❌ Processing failed")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Document information
    if st.session_state.pdf_processor.is_ready():
        st.markdown("### 📊 Document Info")
        doc_info = st.session_state.pdf_processor.get_document_info()
        st.write(f"**Status:** {doc_info['status']}")
        st.write(f"**Chunks:** {doc_info['chunks']}")
        st.write(f"**Embedding:** {doc_info['embedding_type']}")
    
    st.markdown("---")
    
    # Chat controls
    st.markdown("### 🛠️ Chat Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🗑️ Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['pdf_processor', 'history_manager']:
                    del st.session_state[key]
            st.session_state["messages"] = INITIAL_MESSAGE
            st.rerun()
    
    st.markdown("---")
    
    # Recent conversations
    st.markdown("### 📈 Recent Chats")
    history = st.session_state.history_manager.get_history()
    if history:
        st.caption(f"Total conversations: {len(history)}")
        for i, entry in enumerate(reversed(history[-3:])):  # Show last 3
            with st.expander(f"💭 {entry['question'][:25]}...", expanded=False):
                st.caption(f"📄 {entry['filename']}")
                st.caption(f"🕒 {entry['timestamp']}")
    else:
        st.caption("No conversations yet")
    
    st.markdown("---")
    st.markdown(
        "**Note:** <span style='color:#4285f4'>Powered by local Ollama models</span>",
        unsafe_allow_html=True,
    )

# Initialize chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = INITIAL_MESSAGE

if "history" not in st.session_state:
    st.session_state["history"] = []

# Function to display messages with styling
def message_func(content, is_user=False, is_system=False):
    """Display chat messages with custom styling"""
    if is_system:
        st.markdown(f'<div class="system-message">ℹ️ {content}</div>', unsafe_allow_html=True)
    elif is_user:
        st.markdown(f'<div class="user-message">👤 **You:** {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">🤖 **Assistant:** {content}</div>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    message_func(
        message["content"],
        is_user=(message["role"] == "user"),
        is_system=(message["role"] == "system")
    )

# Chat input
if prompt := st.chat_input("Ask a question about your document..."):
    if len(prompt) > 500:
        st.error("Input is too long! Please limit your message to 500 characters.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state["assistant_response_processed"] = False
        
        # Display user message immediately
        message_func(prompt, is_user=True)
        
        # Process response if PDF is ready
        if st.session_state.pdf_processor.is_ready():
            with st.spinner("🤔 Thinking..."):
                try:
                    # Get AI response
                    answer = st.session_state.pdf_processor.ask_question(prompt)
                    
                    # Add assistant message
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                    # Save to history
                    st.session_state.history_manager.add_entry(
                        question=prompt,
                        answer=answer,
                        filename=st.session_state.pdf_processor.get_current_file()
                    )
                    
                    # Display assistant message
                    message_func(answer, is_user=False)
                    
                    st.session_state["assistant_response_processed"] = True
                    
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    message_func(error_msg, is_user=False)
        else:
            # No PDF loaded
            no_pdf_msg = "Please upload and process a PDF document first before asking questions."
            st.session_state.messages.append({"role": "assistant", "content": no_pdf_msg})
            message_func(no_pdf_msg, is_user=False)

# Welcome screen when no messages except initial
if len(st.session_state.messages) <= 2 and not st.session_state.pdf_processor.is_ready():
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px; color: #666;">
        <h3>🚀 Ready to explore your documents?</h3>
        <p>Upload a PDF using the sidebar and start asking questions!</p>
        <br>
        <h4>💡 Example questions to try:</h4>
        <p>• "What is the main topic of this document?"</p>
        <p>• "Can you summarize the key points?"</p>
        <p>• "What are the important dates mentioned?"</p>
        <p>• "Who are the main people discussed?"</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🤖 Powered by Ollama")
with col2:
    st.caption("⚡ Built with Streamlit") 
with col3:
    st.caption("🔒 100% Local Processing")
