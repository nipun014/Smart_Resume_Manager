import json
import argparse
from pathlib import Path

from loader import load_file
from cleaner import clean_text
from parser import split_sections
from extractor import extract_email, extract_phone

from section_parsers import parse_experience, parse_skills


DEFAULT_INPUT = r"D:\projects\cymonic\NIPUN_G_NAIR_Resume.pdf"
DEFAULT_OUTPUT = "parser_output_test.json"


def _parse_args():
    parser = argparse.ArgumentParser(description="Run resume parser pipeline.")
    parser.add_argument("input_file", nargs="?", default=DEFAULT_INPUT, help="Input file path")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output JSON path")
    parser.add_argument(
        "--ocr-mode",
        choices=["fast", "balanced", "accurate"],
        default="balanced",
        help="OCR strategy mode for image inputs: fast, balanced, or accurate.",
    )
    return parser.parse_args()


def main(input_file, output_file, ocr_mode ="balanced"):
    text = load_file(input_file, ocr_mode)
    cleaned = clean_text(text)
    sections = split_sections(cleaned)
    email = extract_email(cleaned)
    phone = extract_phone(cleaned)

    structured = {}

    if "experience" in sections:
        structured["experience"] = parse_experience(sections["experience"])

    if "skills" in sections:
        structured["skills"] = parse_skills(sections["skills"])

    # Step 6: Final output
    output = {
        "contact": {
            "email": email,
            "phone": phone
        },
        "sections": sections,
        "structured": structured
    }

    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Output written to {output_path}")


if __name__ == "__main__":
    args = _parse_args()
    main(args.input_file, args.out, args.ocr_mode)