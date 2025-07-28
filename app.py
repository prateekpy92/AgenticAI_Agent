import streamlit as st
import tempfile, os, warnings
from pdf_processor import PDFProcessor
from history import HistoryManager

warnings.filterwarnings("ignore")

# -------------------------------------------------------------------
# 1.  INITIALISE STATE
# -------------------------------------------------------------------
if "pdf_processor" not in st.session_state:
    st.session_state.pdf_processor = PDFProcessor()
if "history_manager" not in st.session_state:
    st.session_state.history_manager = HistoryManager()

# -------------------------------------------------------------------
# 2.  PAGE CONFIG
# -------------------------------------------------------------------
st.set_page_config(
    page_title="IntelliDoc AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# 3.  ANIMATED / STYLED CSS  ----------------------------------------
# -------------------------------------------------------------------
ANIMATED_CSS = """
<style>
/* ---- Google Font ------------------------------------------------*/
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: "Poppins", sans-serif;
}

/* ---- Global -----------------------------------------------------*/
:root{
  --primary:#6366f1;
  --primary-dark:#4f46e5;
  --bg:#f7f9fc;
  --border:#e5e7eb;
}

.stApp{ background:var(--bg); }

/* ---- HEADER -----------------------------------------------------*/
h1.main-title{
  font-weight:700;
  font-size:2.6rem;
  background:linear-gradient(90deg,#6366f1 0%,#ec4899 100%);
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  animation: hueRotate 8s infinite linear;
  margin-bottom:0.2rem;
}
@keyframes hueRotate{
  0%{filter:hue-rotate(0deg);}
  100%{filter:hue-rotate(360deg);}
}

/* ---- METRICS ----------------------------------------------------*/
.block-container .metric-container{
  background:#fff;
  border:1px solid var(--border);
  border-radius:12px;
  padding:1rem;
  transition:transform .25s ease;
}
.block-container .metric-container:hover{
  transform:translateY(-4px);
  box-shadow:0 6px 18px rgba(0,0,0,0.08);
}

/* ---- SIDEBAR ----------------------------------------------------*/
section[data-testid="stSidebar"]>div{
  border-right:1px solid var(--border);
  background:#fff;
}
.sidebar-button{
  transition:all .25s ease;
}
.sidebar-button:hover{
  background:var(--primary);
  color:#fff !important;
  transform:translateX(2px);
}

/* ---- FILE UPLOADER ---------------------------------------------*/
.stFileUploader>div{
  border:2px dashed var(--primary);
  border-radius:12px;
  background:#fff;
}

/* ---- BUTTONS ----------------------------------------------------*/
button[kind="primary"]{
  background:linear-gradient(135deg,var(--primary) 0%,#ec4899 100%);
  border:none;
}
button[kind="primary"]:hover{
  filter:brightness(1.05);
  transform:scale(1.03);
}

/* ---- CHAT -------------------------------------------------------*/
.stChatMessage{
  animation:fadeInUp .4s ease both;
}
@keyframes fadeInUp{
  from{opacity:0;transform:translateY(20px);}
  to{opacity:1;transform:translateY(0);}
}

/* ---- PROCESS SPINNER -------------------------------------------*/
@keyframes pulse{
  0%{box-shadow:0 0 0 0 rgba(99,102,241,0.4);}
  70%{box-shadow:0 0 0 10px rgba(99,102,241,0);}
  100%{box-shadow:0 0 0 0 rgba(99,102,241,0);}
}
.pulse-btn{
  animation:pulse 2s infinite;
}

/* ---- SCROLLBAR --------------------------------------------------*/
::-webkit-scrollbar{ width:8px;}
::-webkit-scrollbar-thumb{ background:var(--primary); border-radius:8px;}
</style>
"""
st.markdown(ANIMATED_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------------
# 4.  SIDEBAR  ------------------------------------------------------
# -------------------------------------------------------------------
with st.sidebar:
    st.title("🚀 IntelliDoc AI")
    st.caption("Intelligent Document Assistant")
    st.divider()

    # -- Model picker
    st.subheader("🤖 Choose AI model")
    models = {
        "Ollama Llama2": "🦙 Llama2 – General",
        "Ollama Mistral": "⚡ Mistral – Fast",
        "Ollama CodeLlama": "💻 CodeLlama – Code",
        "Ollama Gemma": "💎 Gemma – Latest",
    }
    model = st.radio(
        "Select model",
        list(models.keys()),
        format_func=lambda k: models[k],
        index=0,
    )
    st.session_state["model"] = model

    st.divider()

    # -- Upload
    st.subheader("📄 Upload PDF")
    up_file = st.file_uploader("Pick a PDF", type=["pdf"])
    if up_file and st.button("🚀 Process", key="process_btn", type="primary"):
        with st.spinner("Extracting & embedding …"):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(up_file.read())
            tmp.close()
            ok = st.session_state.pdf_processor.process_pdf(tmp.name, up_file.name)
            os.unlink(tmp.name)
            if ok:
                st.success("Done! Ask me anything about it.")
                st.balloons()
                st.session_state.setdefault("messages", []).append(
                    {"role": "system", "content": f"📄 '{up_file.name}' loaded."}
                )
            else:
                st.error("Processing failed.")

    st.divider()

    # -- Quick actions
    st.subheader("⚙️ Actions")
    col1, col2 = st.columns(2)
    with col1:
        st.button("🔄 Refresh", on_click=lambda: st.rerun(), use_container_width=True)
    with col2:
        def clear_chat():
            st.session_state["messages"] = [
                {"role": "assistant", "content": "Chat cleared – ask away!"}
            ]
        st.button("🗑️ Clear", on_click=clear_chat, use_container_width=True)

    st.divider()

    # -- Recent history
    st.subheader("🕑 Recent questions")
    hist = st.session_state.history_manager.get_history()
    if hist:
        for h in hist[-3:][::-1]:
            st.markdown(f"- **{h['question'][:35]}…**  <br/><span style='font-size:0.75rem'>({h['timestamp'][:19]})</span>",
                        unsafe_allow_html=True)
    else:
        st.caption("No history yet.")

# -------------------------------------------------------------------
# 5.  MAIN AREA  ----------------------------------------------------
# -------------------------------------------------------------------
st.markdown("<h1 class='main-title'>IntelliDoc AI</h1>", unsafe_allow_html=True)
st.write("Upload a PDF and chat with it – now with subtle animations 🎉")

# -- Metrics
c1, c2, c3 = st.columns(3)
c1.metric("📄 Documents", 1 if st.session_state.pdf_processor.is_ready() else 0)
c2.metric("💬 Conversations", len(st.session_state.history_manager.get_history()))
c3.metric("🤖 Model", model.split()[-1])

st.divider()

# -- Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant",
         "content": "👋 Hi! Upload a PDF and start asking me questions."}
    ]

st.subheader("💭 Conversation")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
    else:  # system
        st.info(msg["content"])

# -- Chat input
if prompt := st.chat_input("Ask about your document…"):
    if len(prompt) > 500:
        st.error("Please keep it under 500 chars.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if st.session_state.pdf_processor.is_ready():
            with st.spinner("Thinking…"):
                try:
                    answer = st.session_state.pdf_processor.ask_question(prompt)
                except Exception as e:
                    answer = f"❌ Error: {e}"
                st.session_state.messages.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.write(answer)

                # save to history
                st.session_state.history_manager.add_entry(
                    question=prompt,
                    answer=answer,
                    filename=st.session_state.pdf_processor.get_current_file(),
                )
        else:
            warn = "⚠️ Upload and process a PDF first."
            st.session_state.messages.append({"role": "assistant", "content": warn})
            st.chat_message("assistant").write(warn)

        st.rerun()
