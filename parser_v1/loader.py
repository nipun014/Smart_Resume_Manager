from pathlib import Path
import shutil
import re
import zipfile
import xml.etree.ElementTree as ET
OCR_CONFIGS = {
    "fast":     { "psm_modes": [6],          "try_columns": False },
    "balanced": { "psm_modes": [3, 4, 6, 11], "try_columns": True  },
    "accurate": { "psm_modes": [1, 3, 4, 6, 11], "try_columns": True },
}

def _ocr_single_pass(image, pytesseract, config):
	"""Run one OCR pass and normalize blank output."""
	text = pytesseract.image_to_string(image, config=config)
	return text.strip()


def _ocr_score(text):
	"""Heuristic quality score: reward useful text, penalize noisy symbols."""
	if not text:
		return 0.0
	lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
	if not lines:
		return 0.0
	char_count = sum(len(ln) for ln in lines)
	alpha_count = sum(ch.isalpha() for ch in text)
	word_count = len(re.findall(r"\b[A-Za-z]{2,}\b", text))
	single_char_tokens = len(re.findall(r"\b[A-Za-z]\b", text))
	
	# Expanded set of noise characters that indicate OCR errors
	noise_chars = set("|=~^`§¶†‡©®™€¥£¢¤¦¬µ∞∑∂√∆∫≠≤≥±×÷")
	noise_count = sum(ch in noise_chars for ch in text)

	lower = text.lower()
	resume_headers = [
		"summary", "skills", "education", "experience", "work history",
		"projects", "certifications", "languages", "contact",
	]
	header_hits = sum(1 for h in resume_headers if h in lower)

	has_email = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
	has_phone = bool(re.search(r"(\+\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}", text))
	
	line_bonus = min(len(lines), 120) * 3
	structure_bonus = header_hits * 35 + (45 if has_email else 0) + (30 if has_phone else 0)
	readability_penalty = single_char_tokens * 4

	return (
		char_count * 0.45
		+ alpha_count * 0.2
		+ word_count * 7
		+ line_bonus
		+ structure_bonus
		- noise_count * 6
		- readability_penalty
	)


def _ocr_image_text(image, pytesseract, ocr_mode="balanced"):
	"""Extract text with a two-column fallback for resume-like layouts."""
	from PIL import Image, ImageOps

	# Basic cleanup improves contrast for scanned resumes.
	gray = ImageOps.grayscale(image)
	if gray.width < 1200:
		gray = gray.resize((gray.width * 2, gray.height * 2), resample=Image.Resampling.LANCZOS)
	boosted = ImageOps.autocontrast(gray)
	inverted = ImageOps.invert(boosted)
	binary = boosted.point(lambda p: 255 if p > 165 else 0)
	binary_inverted = ImageOps.invert(binary)

	candidates = []
	config= OCR_CONFIGS[ocr_mode]
	for variant in (boosted, inverted, binary, binary_inverted):
		for psm in config["psm_modes"]:
			candidates.append(_ocr_single_pass(variant, pytesseract, config=f"--oem 3 --psm {psm}"))

	best = max(candidates, key=_ocr_score)

	width, height = boosted.size
	# Treat portrait documents as likely multi-column and OCR each half.
	if config["try_columns"] and width * 1.15 < height and width >= 600:
		
	
		overlap = max(16, width // 40)
		mid = width // 2
		left_box = (0, 0, min(width, mid + overlap), height)
		right_box = (max(0, mid - overlap), 0, width, height)

		left_text = _ocr_single_pass(boosted.crop(left_box), pytesseract, config="--oem 3 --psm 4")
		right_text = _ocr_single_pass(boosted.crop(right_box), pytesseract, config="--oem 3 --psm 4")
		left_inv = _ocr_single_pass(inverted.crop(left_box), pytesseract, config="--oem 3 --psm 11")
		right_inv = _ocr_single_pass(inverted.crop(right_box), pytesseract, config="--oem 3 --psm 11")
		left_bin = _ocr_single_pass(binary.crop(left_box), pytesseract, config="--oem 3 --psm 6")
		right_bin = _ocr_single_pass(binary.crop(right_box), pytesseract, config="--oem 3 --psm 6")
		left_bin_inv = _ocr_single_pass(binary_inverted.crop(left_box), pytesseract, config="--oem 3 --psm 6")
		right_bin_inv = _ocr_single_pass(binary_inverted.crop(right_box), pytesseract, config="--oem 3 --psm 6")

		column_text = "\n\n".join(part for part in (left_text, right_text) if part)
		column_inverted = "\n\n".join(part for part in (left_inv, right_inv) if part)
		column_binary = "\n\n".join(part for part in (left_bin, right_bin) if part)
		column_binary_inverted = "\n\n".join(part for part in (left_bin_inv, right_bin_inv) if part)

		# Gap-aware split can improve two-column extraction when center area is noisy.
		gap = max(24, width // 18)
		left_gap_box = (0, 0, max(1, mid - gap), height)
		right_gap_box = (min(width - 1, mid + gap), 0, width, height)

		left_gap = _ocr_single_pass(boosted.crop(left_gap_box), pytesseract, config="--oem 3 --psm 4")
		right_gap = _ocr_single_pass(boosted.crop(right_gap_box), pytesseract, config="--oem 3 --psm 4")
		left_gap_bin = _ocr_single_pass(binary_inverted.crop(left_gap_box), pytesseract, config="--oem 3 --psm 6")
		right_gap_bin = _ocr_single_pass(binary_inverted.crop(right_gap_box), pytesseract, config="--oem 3 --psm 6")
		column_gap_text = "\n\n".join(part for part in (left_gap, right_gap) if part)
		column_gap_binary = "\n\n".join(part for part in (left_gap_bin, right_gap_bin) if part)

		best = max(
			[
				best,
				column_text,
				column_inverted,
				column_binary,
				column_binary_inverted,
				column_gap_text,
				column_gap_binary,
			],
			key=_ocr_score,
		)

	return best


def _normalize_docx_text(value):
	"""Collapse excessive whitespace while preserving line breaks."""
	lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
	return "\n".join(line for line in lines if line)


def _extract_docx_text(path):
	"""Extract text from .docx via python-docx when available, else XML fallback."""
	try:
		from docx import Document  # type: ignore

		doc = Document(str(path))
		paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
		return "\n".join(paragraphs)
	except Exception:
		# Fallback parser reads the main WordprocessingML document body.
		with zipfile.ZipFile(path) as archive:
			with archive.open("word/document.xml") as xml_file:
				root = ET.fromstring(xml_file.read())

		ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
		lines = []
		for para in root.findall(".//w:p", ns):
			parts = []
			for node in para.findall(".//w:t", ns):
				if node.text:
					parts.append(node.text)
			if parts:
				lines.append("".join(parts))

		return "\n".join(lines)


def load_file(file_path, ocr_mode ="balanced"):
	"""Load text from a .txt, .pdf, .docx, .jpg, .jpeg, or .png file path."""
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f"File not found: {file_path}")

	suffix = path.suffix.lower()
	if suffix == ".txt":
		return path.read_text(encoding="utf-8", errors="ignore")

	if suffix == ".pdf":
		try:
			from pypdf import PdfReader
		except ImportError as exc:
			raise ImportError(
				"PDF support requires pypdf. Install it with: pip install pypdf"
			) from exc

		reader = PdfReader(str(path))
		pages_text = []
		for page in reader.pages:
			pages_text.append(page.extract_text() or "")
		return "\n".join(pages_text)

	if suffix == ".docx":
		try:
			text = _extract_docx_text(path)
		except KeyError as exc:
			raise RuntimeError("Invalid DOCX file: missing word/document.xml") from exc
		except Exception as exc:
			raise RuntimeError("Failed to read DOCX content.") from exc

		return _normalize_docx_text(text)

	if suffix in {".jpg", ".jpeg", ".png"}:
		try:
			from PIL import Image
		except ImportError as exc:
			raise ImportError(
				"Image support requires Pillow. Install it with: pip install pillow"
			) from exc

		try:
			import pytesseract
		except ImportError as exc:
			raise ImportError(
				"Image OCR requires pytesseract. Install it with: pip install pytesseract"
			) from exc

		# Resolve the Tesseract binary for Windows installs when PATH is not refreshed.
		tesseract_exe = shutil.which("tesseract")
		if not tesseract_exe:
			common_paths = [
				Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
				Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
			]
			for candidate in common_paths:
				if candidate.exists():
					tesseract_exe = str(candidate)
					break

		if tesseract_exe:
			pytesseract.pytesseract.tesseract_cmd = tesseract_exe
		else:
			raise RuntimeError(
				"Tesseract OCR executable was not found. Install Tesseract and ensure the "
				"binary is on PATH, or set pytesseract.pytesseract.tesseract_cmd to its full path."
			)

		try:
			with Image.open(path) as img:
				return _ocr_image_text(img, pytesseract, ocr_mode)
		except Exception as exc:
			raise RuntimeError(
				"Failed to OCR image. Make sure Tesseract OCR is installed and in PATH."
			) from exc

	raise ValueError(
		f"Unsupported file type: {suffix}. Use .txt, .pdf, .docx, .jpg, .jpeg, or .png"
	)
    
