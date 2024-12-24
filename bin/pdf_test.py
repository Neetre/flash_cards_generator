import io
import PyPDF2

from PIL import Image
import pytesseract
import fitz  # PyMuPDF

def extract_text_from_image_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image = Image.open(io.BytesIO(image_bytes))
            text += pytesseract.image_to_string(image)
    return text

def read_pdf(pdf_path):
    """
    Reads the text content of a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        A string containing the extracted text, or None if an error occurs.
    """
    try:
        with open(pdf_path, 'rb') as file:  # Open in binary read mode
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            text = ""
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
            return text
    except FileNotFoundError:
        print(f"Error: File not found at {pdf_path}")
        return None
    except PyPDF2.errors.PdfReadError: #Handle corrupted or invalid PDFs
        print(f"Error: Could not read PDF at {pdf_path}. It might be corrupted or encrypted.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


if __name__ == "__main__":
    pdf_file_path = "../data/wwi_russia.pdf"  # Replace with the actual path
    extracted_text = extract_text_from_image_pdf(pdf_file_path)

    if extracted_text:
        # Process the extracted text as needed
        #For example print it to the console or write it to a file
        print(extracted_text)

        #Example of writing to a text file
        output_file_path = "output.txt"
        try:
            with open(output_file_path, "w", encoding="utf-8") as outfile: #Important to specify utf-8 encoding
                outfile.write(extracted_text)
            print(f"Text successfully written to {output_file_path}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("Failed to extract text from PDF.")