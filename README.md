# RESUME IQ Smart Talen Selection



## The Problem
Recruiters and hiring teams often spend significant time manually reviewing resumes against a job description, especially when resumes come in mixed formats such as PDF, DOCX, TXT, and images. This manual process is slow, inconsistent, and makes it harder to quickly identify the strongest candidates based on required skills and role fit.

## What It Does
- Upload multiple resumes and a single job description.
- Extract skills, experience, and profile signals from each resume.
- Score candidates with keyword and semantic matching.
- Generate a short justification for the top-ranked candidates.

## Tech Stack
- Python
- Flask
- sentence-transformers
- scikit-learn
- python-dotenv
- google-genai
- pypdf
- python-docx
- Pillow
- pytesseract

## Deployment Notes
- The app is Vercel-compatible for text, PDF, and DOCX resumes.
- Image OCR is not reliable on Vercel because the platform does not provide native Tesseract.
- Temporary uploads now go to the system temp directory instead of the repo `uploads/` folder.
- Set `GEMINI_API_KEY` in Vercel environment variables if you want AI justifications.

## Local Setup
### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the app locally

```powershell
python app/app.py
```

Open:

- `http://127.0.0.1:5000`

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
