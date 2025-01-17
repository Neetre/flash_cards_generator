import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from groq import Groq
import pytesseract
from pdf2image import convert_from_path
import pytesseract
import base64
import google.generativeai as genai


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


scanner_model = genai.GenerativeModel("gemini-1.5-flash")

@dataclass
class FlashCard:
    prompt: str
    answer: str
    category: Optional[str] = None
    difficulty: Optional[str] = None


class AnalyzeDocs:
    def __init__(self, target_language="english", model="mixtral-8x7b-32768"):
        self.target_language = target_language.lower()
        self.model = model
        self.client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable not set")

    def generate_with_groq(self, messages: List[Dict[str, str]], retry_count=3) -> str:
        """Generate content using the GROQ API with retry logic.
        
        Args:
            messages (List[Dict[str, str]]): A list of messages to send to the API.
            retry_count (int): The number of times to retry the request.
        
        Returns:
            str: The generated content.
        """
        for attempt in range(retry_count):
            try:
                completion = self.client_groq.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=0.7,
                )
                return completion.choices[0].message.content
            except Exception as e:
                if attempt == retry_count - 1:
                    raise Exception(f"Failed to generate content after {retry_count} attempts: {str(e)}")
                continue

    def extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts and terminology from the text.
        
        Args:
            text (str): The text content to analyze.
            
        Returns:
            List[str]: A list of key concepts and terminology.
        """
        messages = [
            {"role": "system", "content": """Extract key concepts and terminology from the text. 
Return the result as a JSON array of strings. Each string should be a key concept or term."""},
            {"role": "user", "content": text}
        ]
        response = self.generate_with_groq(messages)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    def categorize_content(self, text: str) -> str:
        """Determine the subject category of the content.
        
        Args:
            text (str): The text content to categorize.
        
        Returns:
            str: The category name.
        """
        messages = [
            {"role": "system", "content": """Determine the main subject category of the content. 
Choose from the following categories: History, Science, Math, Literature, Art, Technology, Biology, Chemistry, Physics, Geography or Other.
Return only the category name as a string.
"""},
            {"role": "user", "content": text}
        ]
        response = self.generate_with_groq(messages)
        return response
    
    def summarize_text(self, text: str) -> str:
        """Summarize long text into key points.
        
        Args:
            text (str): The text to summarize.
        
        Returns:
            str: The summarized text.
        """
        messages = [
            {"role": "system", "content": """Summarize the following text into key points. 
Return the summary as a bullet-point list. Each bullet point should be concise and capture a main idea."""},
            {"role": "user", "content": text}
        ]
        response = self.generate_with_groq(messages)
        return response
        
    def generate_qa_pairs(self, summary: str) -> List[Dict[str, str]]:
        """Generate relevant Q&A pairs from the summary.
        
        Args:
            summary (str): The summary text.
        
        Returns:
            List[Dict[str, str]]: A list of question-answer pairs.
        """
        messages = [
            {"role": "system", "content": """Generate 3 relevant question-answer pairs from this text. 
Return the result as a JSON array. Each object in the array should have 'question' and 'answer' fields. 
The questions should be clear and the answers should be concise."""},
            {"role": "user", "content": summary}
        ]
        response = self.generate_with_groq(messages)
        try:
            response = response.strip()
            if not response.startswith('['):
                response = response[response.find('['):]
            if not response.endswith(']'):
                response = response[:response.rfind(']')+1]
            return json.loads(response)
        except json.JSONDecodeError:
            print("Warning: Could not parse JSON response. Returning empty list.")
            return []
        
    def translate_content(self, content: str) -> str:
        """Translate content to target language.
        
        Args:
            content (str): The content to translate.
        
        Returns:
            str: The translated content.
        """
        if self.target_language.lower() == "english":
            return content
        print(f"Translating content to {self.target_language}...")
        translate_model=genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=f"Translate the following text to {self.target_language}. Return only the translated text.")
        result = translate_model.generate_content(content).text
        return result

    def create_lesson(self, text):
        """Create a lesson from text content.
        
        Args:
            text (str): The text content to create a lesson from.
        
        Returns:
            str: The lesson content.
        """
        lesson_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Create a lesson from the following text. Return the lesson content.")
        return lesson_model.generate_content(text).text

    def process_document(self, text: str, num_cards: int = 3) -> List[FlashCard]:
        """Process document and generate flash cards with difficulty levels and categories.
        
        Args:
            text (str): The text content to process.
            num_cards (int): The number of flash cards to generate.
        
        Returns:
            List[FlashCard]: A list of FlashCard objects.
        """
        category = self.categorize_content(text)
        summary = self.summarize_text(text)
        key_concepts = self.extract_key_concepts(text)

        messages = [
            {"role": "system", "content": f"""Generate {num_cards} flash cards based on the following text. 
Focus on the key concepts: {', '.join(key_concepts)}. 
Return the result as a JSON array. Each object in the array should have the following fields: 
'question', 'answer', 'difficulty' (easy/medium/hard). 
The questions should be clear and the answers should be concise."""},
            {"role": "user", "content": summary}
        ]
        
        response = self.generate_with_groq(messages)
        try:
            qa_pairs = json.loads(response)
        except json.JSONDecodeError:
            return []

        try:
            combined_content = '\n'.join([" ".join([qa['question'], qa['answer']]) for qa in qa_pairs])
            translated_content = self.translate_content(combined_content).split('\n')
        except Exception as e:
            print(f"Error translating content: {str(e)}")
            translated_content = [qa['question'] for qa in qa_pairs] + [qa['answer'] for qa in qa_pairs]
        try:
            flash_cards = []
            for i, qa in enumerate(qa_pairs[:num_cards]):
                translated_q, translated_a = translated_content[i].split('? ', 1)

                card = FlashCard(
                    prompt=translated_q+'?',
                    answer=translated_a,
                    category=category,
                    difficulty=qa.get('difficulty', 'medium')
                )
                flash_cards.append(card)
        except Exception as e:
            print(f"Error creating flash cards: {str(e)}")
            flash_cards = []
        return flash_cards

    def save_flashcards(self, cards: List[FlashCard], filename: str):
        """Save flash cards to a JSON file.
        
        Args:
            cards (List[FlashCard]): A list of FlashCard objects.
            filename (str): The name of the file to save the flash cards.
        """
        data = []
        for card in cards:
            data.append({
                "prompt": card.prompt,
                "answer": card.answer,
                "category": card.category,
                "difficulty": card.difficulty
            })
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Flash cards saved to {filename}")

    def load_flashcards(self, filename: str) -> List[FlashCard]:
        """Load flash cards from a JSON file.
        
        Args:
            filename (str): The name of the file to load the flash cards from.
        
        Returns:
            List[FlashCard]: A list of FlashCard objects.
        """
        cards = []
        with open(filename, 'r') as file:
            data = json.load(file)
        for item in data:
            card = FlashCard(
                prompt=item['prompt'],
                answer=item['answer'],
                category=item.get('category'),
                difficulty=item.get('difficulty')
            )
            cards.append(card)
        return cards

    def generate_flashcards(self, text: str, num_cards: int = 3, language: str = None, save_to: str = None) -> List[FlashCard]:
        """Generate flash cards from text content.
        
        Args:
            text (str): The text content to generate flash cards from.
            num_cards (int): The number of flash cards to generate.
            save_to (str): The filename to save the flash cards to.
        
        Returns:
            List[FlashCard]: A list of FlashCard objects.
        """
        self.target_language = language if language is not None else self.target_language
        cards = self.process_document(text, num_cards)
        if save_to:
            self.save_flashcards(cards, save_to)
        return cards
    
    def flashcards_to_json(self, cards: List[FlashCard]) -> List[Dict[str, str]]:
        """Convert a list of FlashCard objects to a JSON format.
        
        Args:
            cards (List[FlashCard]): A list of FlashCard objects.
        
        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the flash cards.
        """
        data = []
        for card in cards:
            data.append({
                "prompt": card.prompt,
                "answer": card.answer,
                "category": card.category,
                "difficulty": card.difficulty
            })
        return data

    def generate_flashcards_from_file(self, filename: str, num_cards: int = 3, save_to: str = None) -> List[FlashCard]:
        """Generate flash cards from a text file.
        
        Args:
            filename (str): The name of the file to generate flash cards from.
            num_cards (int): The number of flash cards to generate.
            save_to (str): The filename to save the flash cards to.
        
        Returns:
            List[FlashCard]: A list of FlashCard objects.
        """
        with open(filename, 'r') as file:
            text = file.read()
        return self.generate_flashcards(text, num_cards, save_to)


class ReadDocs:
    def __init__(self, data_dir="input"):
        self.data_dir = data_dir

    def read_pdf_with_gemini(self, file_path: str) -> str:
        """Read text content from a PDF file using the Gemini API.
        
        Args:
            file_path (str): The path to the PDF file.
            language (str): The language of the text.
        
        Returns:
            str: The text content of the PDF.
        """
        with open(file_path, "rb") as doc_file:
            doc_data = base64.standard_b64encode(doc_file.read()).decode("utf-8")
        prompt = "Extract the content from the PDF document."
        response = scanner_model.generate_content([{'mime_type': 'application/pdf', 'data': doc_data}, prompt])
        return response.text

    def read_pdf(self, file_path: str, lang: str = "eng") -> str:
        """Read text content from a PDF file.
        
        Args:
            file_path (str): The path to the PDF file.
        
        Returns:
            str: The text content of the PDF.
        """
        images = convert_from_path(file_path)

        text = ""
        for image in images:
            text += pytesseract.image_to_string(image, lang=lang)
        return text
        
    def read_text(self, file_path: str) -> str:
        """Read text content from a text file.
        
        Args:
            file_path (str): The path to the text file.
        
        Returns:
            str: The text content of the file.
        """
        with open(file_path, 'r') as file:
            return file.read()

    def read_document(self, file_type: str, file_name: str) -> str:
        """Read text content from a document file.
        
        Args:
            file_type (str): The type of file (pdf or text).
            file_nae (str): The name of the file.
        
        Returns:
            str: The text content of the document.
        """
        file_path = os.path.join(self.data_dir, file_name)
        if file_type == "pdf":
            return self.read_pdf(file_path)
        elif file_type == "text":
            return self.read_text(file_path)
        else:
            raise ValueError("Invalid file type. Only PDF and text files are allowed.")