from pathlib import Path
import shutil


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
	noise_count = sum(ch in "|=~^`" for ch in text)
	line_bonus = min(len(lines), 120) * 3
	return char_count + alpha_count * 0.25 + line_bonus - noise_count * 5


def _ocr_image_text(image, pytesseract):
	"""Extract text with a two-column fallback for resume-like layouts."""
	from PIL import Image, ImageOps

	# Basic cleanup improves contrast for scanned resumes.
	gray = ImageOps.grayscale(image)
	if gray.width < 1200:
		gray = gray.resize((gray.width * 2, gray.height * 2), resample=Image.Resampling.LANCZOS)
	boosted = ImageOps.autocontrast(gray)
	inverted = ImageOps.invert(boosted)

	candidates = []
	for variant in (boosted, inverted):
		candidates.append(_ocr_single_pass(variant, pytesseract, config="--oem 3 --psm 6"))
		candidates.append(_ocr_single_pass(variant, pytesseract, config="--oem 3 --psm 11"))

	best = max(candidates, key=_ocr_score)

	width, height = boosted.size
	# Treat portrait documents as likely multi-column and OCR each half.
	if width * 1.15 < height and width >= 600:
		overlap = max(16, width // 40)
		mid = width // 2
		left_box = (0, 0, min(width, mid + overlap), height)
		right_box = (max(0, mid - overlap), 0, width, height)

		left_text = _ocr_single_pass(boosted.crop(left_box), pytesseract, config="--oem 3 --psm 4")
		right_text = _ocr_single_pass(boosted.crop(right_box), pytesseract, config="--oem 3 --psm 4")
		left_inv = _ocr_single_pass(inverted.crop(left_box), pytesseract, config="--oem 3 --psm 11")
		right_inv = _ocr_single_pass(inverted.crop(right_box), pytesseract, config="--oem 3 --psm 11")

		column_text = "\n\n".join(part for part in (left_text, right_text) if part)
		column_inverted = "\n\n".join(part for part in (left_inv, right_inv) if part)
		best = max([best, column_text, column_inverted], key=_ocr_score)

	return best


def load_file(file_path):
	"""Load text from a .txt, .pdf, .jpg, .jpeg, or .png file path."""
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
				return _ocr_image_text(img, pytesseract)
		except Exception as exc:
			raise RuntimeError(
				"Failed to OCR image. Make sure Tesseract OCR is installed and in PATH."
			) from exc

	raise ValueError(
		f"Unsupported file type: {suffix}. Use .txt, .pdf, .jpg, .jpeg, or .png"
	)
    
