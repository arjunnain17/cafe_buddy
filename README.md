# Cafe Buddy

An NLP-powered cafe menu recommendation CLI using Gemini Embeddings and FAISS vector search.

## Setup

1. **Clone repository & enter directory**
   ```bash
   git clone <repo_url>
   cd Cafe_buddy
   ```

2. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY="your_api_key_here"
   ```

4. **Create Data Storage**
   Create the directory where FAISS will save its embedding indexes:
   ```bash
   mkdir storage
   ```

## Usage

1. **Customize the Menu (Optional)**
   Edit the Python list of dictionaries located in `data/menu.py` to add, remove, or change drinks and their descriptions.

2. **Generate Vector Index** 
   Run this once initially, and re-run it anytime you update `data/menu.py`.
   ```bash
   python core/ingest.py
   ```

3. **Start Interactive CLI**
   ```bash
   python app.py
   ```
