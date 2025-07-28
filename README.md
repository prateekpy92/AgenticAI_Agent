IntelliDoc AI
=============

A modern Streamlit app for intelligent, AI-powered PDF document Q&A and analysis using local models (Ollama).

Features
--------
- Upload any PDF document.
- Choose from multiple local AI models (Llama2, Mistral, CodeLlama, Gemma).
- Ask questions or chat with your document. Get instant, contextual, AI-powered answers.
- All processing runs locally – data stays on your machine (privacy friendly).
- Conversation history and system status available in the sidebar.
- Animated, modern UI with gradients, hover effects, and chat-style conversation display.

Quick Start
-----------
1. Install required packages and dependencies:
    - `streamlit`
    - Any other Python packages needed by `pdf_processor.py` and `history.py`
    - Ensure Ollama and desired local AI models are installed/running (see below)

2. Place your `pdf_processor.py` and `history.py` modules in the same directory as this app.
   Make sure they provide a `PDFProcessor` and `HistoryManager` class as used in the app.

3. Run the app:
    ```
    streamlit run app.py
    ```
   (Replace `app.py` with the name of your main script if different.)

4. Open the local URL printed by Streamlit in your browser.
   - Use the sidebar to select a model and upload a PDF.
   - Once processed, ask questions about your document in the chat input.
   - Recent queries and system info will appear in the sidebar.

Dependencies
------------
- Python 3.8+
- streamlit
- Your own code for:
    - `pdf_processor.py`: Must provide PDFProcessor (should have methods is_ready, process_pdf, ask_question, get_current_file, get_document_info)
    - `history.py`: Must provide HistoryManager (should have methods get_history, add_entry)
- Any packages required by your pdf processing/model code
- Ollama (for running supported LLMs locally, see below)

AI Model Setup
--------------
This app uses local AI models via [Ollama](https://ollama.com/) for document understanding and chat.
**You must have Ollama installed and running, and the desired models pulled locally, before using IntelliDoc AI.**

1. **Install Ollama**

   Download Ollama for your operating system from:  
   https://ollama.com/download

   Make sure you can run the `ollama` command from your terminal.

2. **Download (Pull) the Models Used**

   Open your terminal and pull the required models by running:

ollama pull llama2
ollama pull mistral
ollama pull codellama
ollama pull gemma


- `llama2`     = General purpose chat model  
- `mistral`    = Fast, efficient model  
- `codellama`  = Code understanding/generation  
- `gemma`      = Google's latest open LLM

This process may take several minutes (and will use disk space, ~4–8GB per model depending on version).

3. **Check Models are Available**

You can check your models with:


ollama list   ->for listing downloaded models


All models required for IntelliDoc AI should appear as "AVAILABLE".

4. **(Optional) Use Other Models**

- To use additional/different models, update the `models` dictionary in `app.py`, and make sure to pull with `ollama pull <model-name>`.

Customization
-------------
- All styling and animations are handled in a single CSS block in the Python file. Edit or extend this section to change the look and feel.
- To add more AI models or change logic, update the `models` dictionary and handling in the app.
- For new features, edit the corresponding Streamlit sidebar and main area code.

Notes
-----
- No data is sent to the cloud. All processing is on-device, assuming your models run locally (like with Ollama).
- Animations and effects use pure CSS inside the Python main file.
- Works with all modern desktop browsers.

Support
-------
For questions or issues, check your custom code (`pdf_processor.py`, `history.py`) and see the Streamlit and Ollama documentation.

Enjoy using IntelliDoc AI!
