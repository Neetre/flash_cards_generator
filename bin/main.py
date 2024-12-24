import json
from pypdf import PdfReader

from dotenv import load_dotenv
load_dotenv()

from model import AnalyzeDocs


def read_pdf(file_path):
    reader = PdfReader(file_path)
    print("Num pages: ", len(reader.pages))
    return reader.pages[0].extract_text()


def read_text(file: str) -> str:
    with open(file, 'r') as f:
        return f.read()
    

def main():
    analyze = AnalyzeDocs()
    text = read_text("../data/sample_text.txt")
    flash_cards = analyze.process_document(text)
    print(flash_cards)


if __name__ == "__main__":
    main()
