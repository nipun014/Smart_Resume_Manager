# Smart Resume Manager

## Project Title
Cymonic Resume-JD Smart Matcher

## The Problem
Recruiters and hiring teams often spend significant time manually reviewing resumes against a job description, especially when resumes come in mixed formats such as PDF, DOCX, TXT, and images. This manual process is slow, inconsistent, and makes it harder to quickly identify the strongest candidates based on required skills and role fit.

## The Solution
This project provides an end-to-end resume screening workflow that compares multiple resumes against a single job description and ranks candidates by match score. It combines keyword-based skill matching with semantic similarity scoring, then generates short AI-powered justification text for top candidates.

Key features:
- Multi-format resume ingestion: TXT, PDF, DOCX, JPG, JPEG, PNG
- OCR support for image resumes, including improved handling for two-column layouts
- Job description skill extraction with alias normalization
- Hybrid scoring model:
  - Keyword score from extracted JD and candidate skills
  - Semantic score from sentence embeddings and cosine similarity
- Weighted final ranking and top-candidate justification output
- Simple Flask web UI for uploading resumes and viewing ranked results

## Tech Stack
### Programming Languages
- Python
- HTML
- CSS

### Frameworks and Libraries
- Flask
- sentence-transformers
- scikit-learn
- python-dotenv
- google-genai
- pypdf
- python-docx
- Pillow
- pytesseract

### Database
- No database (file-based processing in memory/runtime)

### APIs and Third-Party Tools
- Google Gemini API (for candidate justification generation)
- Tesseract OCR engine (native executable used by pytesseract)

## Setup Instructions
### 1. Create and activate a virtual environment
Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install flask sentence-transformers scikit-learn python-dotenv google-genai pypdf python-docx pillow pytesseract
```

### 3. Configure environment variables
Create a `.env` file in the project root with:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Install Tesseract OCR (required for image resumes)
- Windows: install Tesseract OCR and ensure `tesseract.exe` is on PATH.
- The loader also checks these common paths automatically:
  - `C:/Program Files/Tesseract-OCR/tesseract.exe`
  - `C:/Program Files (x86)/Tesseract-OCR/tesseract.exe`

### 5. Run the Flask app locally
From the project root:

```powershell
python app/app.py
```

Open your browser at:
- `http://127.0.0.1:5000`

### 6. (Optional) Run the parser pipeline directly

```powershell
python parser_v1/main.py "path/to/resume.pdf" --out parser_output_test.json --ocr-mode balanced
```

OCR mode options:
- `fast`
- `balanced`
- `accurate`

## Notes
- If Gemini API quota/rate-limit issues occur, the app falls back gracefully and still returns ranking results.
- Resume upload temp files are stored in `uploads/` during processing and cleaned up after each request.
