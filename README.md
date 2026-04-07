# RESUME IQ - Smart Talent Selection

Automated resume screening and candidate matching system that uses keyword and semantic analysis to rank candidates against job descriptions.

## The Problem
Recruiters and hiring teams often spend significant time manually reviewing resumes against a job description, especially when resumes come in mixed formats such as PDF, DOCX, TXT, and images. This manual process is slow, inconsistent, and makes it harder to quickly identify the strongest candidates based on required skills and role fit.

## The Solution
RESUME IQ automates the resume screening process by leveraging both keyword matching and semantic analysis. The platform extracts skills, experience, and profile signals from multiple resumes in various formats, then scores each candidate using a hybrid approach that identifies keyword matches and semantic similarity to the job requirements. Key features include:
- Multi-format resume support (PDF, DOCX, TXT, images with OCR)
- Automated skill extraction and profile building
- Dual-scoring system: keyword-based + semantic matching
- AI-powered justifications for top candidates
- Vercel-compatible deployment with optional local OCR support

## What It Does
- Upload multiple resumes and a single job description.
- Extract skills, experience, and profile signals from each resume.
- Score candidates with keyword and semantic matching.
- Generate a short justification for the top-ranked candidates.

## Tech Stack
- **Programming Language:** Python
- **Web Framework:** Flask
- **NLP & ML:** sentence-transformers, scikit-learn
- **APIs & Services:** google-genai (Gemini API)
- **Document Processing:** pypdf, python-docx, Pillow, pytesseract
- **Environment Management:** python-dotenv
- **Deployment:** Vercel (serverless)

## Deployment Notes
- The app is Vercel-compatible for text, PDF, and DOCX resumes.
- Image OCR is not reliable on Vercel because the platform does not provide native Tesseract.
- Temporary uploads now go to the system temp directory instead of the repo `uploads/` folder.
- Set `GEMINI_API_KEY` in Vercel environment variables if you want AI justifications.

## Setup Instructions

### Install Dependencies
**Prerequisites:** Python 3.8+ installed on your system

1. **Clone the repository:**
```bash
git clone <repository-url>
cd cymonic
```

2. **Create a virtual environment:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. **Install required packages:**
```powershell
pip install -r requirements.txt
```

### Run the Project Locally

1. **Configure environment variables**
Create a `.env` file in the project root with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

2. **Start the application:**
```powershell
python app/app.py
```

3. **Access the web interface:**
Open your browser and navigate to `http://127.0.0.1:5000`

## Deploying to Vercel
### 1. Push the repository to GitHub
Vercel deploys cleanly from a GitHub repository.

### 2. Import the repo in Vercel
In the Vercel dashboard, choose New Project and import this repository.

### 3. Keep the defaults
Use the Python runtime that Vercel detects automatically. No custom build command is required for this project.

### 4. Add environment variables
Set `GEMINI_API_KEY` in the Vercel project settings.

### 5. Deploy
After deployment, open the generated Vercel URL and test with a TXT, PDF, or DOCX resume first.

## Project Structure
- `app/` - Flask routes and templates wiring
- `parser_v1/` - resume parsing and text extraction
- `profile/` - candidate profile building
- `scoring/` - scoring and justification logic
- `api/index.py` - Vercel entrypoint
- `vercel.json` - Vercel routing config

## Notes
- Gemini quota or rate-limit errors fall back gracefully, so scoring still works.
- For image resumes, run the app locally or on a host where Tesseract is installed.
