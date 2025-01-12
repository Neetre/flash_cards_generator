import json
from pypdf import PdfReader

from model import AnalyzeDocs


def read_pdf(file_path):
    reader = PdfReader(file_path)
    print("Num pages: ", len(reader.pages))
    pagina = reader.pages[1]
    return pagina.extract_text()


def read_text(file: str) -> str:
    with open(file, 'r') as f:
        return f.read()
    

def main():
    # text = read_pdf("../data/wwi_russia.pdf")
    # print(text)
    analyze = AnalyzeDocs()
    text = read_text("../data/sample_text.txt")
    print(text)
    flash_cards = analyze.process_document(text)
    print(flash_cards)


if __name__ == "__main__":
    main()
