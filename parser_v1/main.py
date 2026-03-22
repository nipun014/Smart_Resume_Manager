from loader import load_file
from cleaner import clean_text
from parser import split_sections
from extractor import extract_email

file_path = r"D:\projects\cymonic\image_resume_2.jpg"


def main():
	text = load_file(file_path)
	cleaned = clean_text(text)
	sections = split_sections(cleaned)
	email = extract_email(cleaned)

	print("EMAIL:", email)
	print("SECTIONS:")
	for name, content in sections.items():
		print(f"\n[{name}]")
		print(content[:300])


if __name__ == "__main__":
	main()