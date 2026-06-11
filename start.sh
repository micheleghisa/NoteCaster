#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "Avvio Personal NotebookLM su http://localhost:8501"
streamlit run app.py --server.port 8501 --server.headless false
