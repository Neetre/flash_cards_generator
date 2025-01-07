import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from groq import Groq


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
            {"role": "system", "content": "Extract key concepts and terminology from the text. Return as JSON array."},
            {"role": "user", "content": text}
        ]
        response = self.generate_with_groq(messages)
        print(response)
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
            {"role": "system", "content": "Determine the main subject category (e.g., 'History', 'Science', 'Math'). Return only the category name."},
            {"role": "user", "content": text}
        ]
        response = self.generate_with_groq(messages)
        print(response)
        return response
    
    def summarize_text(self, text: str) -> str:
        """Summarize long text into key points.
        
        Args:
            text (str): The text to summarize.
        
        Returns:
            str: The summarized text.
        """
        messages = [
            {"role": "system", "content": "Summarize the following text into key points."},
            {"role": "user", "content": text}
        ]
        response = self.generate_with_groq(messages)
        print(response)
        return response
        
    def generate_qa_pairs(self, summary: str) -> List[Dict[str, str]]:
        """Generate relevant Q&A pairs from the summary.
        
        Args:
            summary (str): The summary text.
        
        Returns:
            List[Dict[str, str]]: A list of question-answer pairs.
        """
        messages = [
            {"role": "system", "content": "Generate 3 relevant question-answer pairs from this text. Return as JSON array with 'question' and 'answer' fields."},
            {"role": "user", "content": summary}
        ]
        response = self.generate_with_groq(messages)
        print(response)
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

        messages = [
            {"role": "system", "content": f"Translate the following text to {self.target_language}, maintaining any technical terms appropriate for a school context."},
            {"role": "user", "content": content}
        ]
        result = self.generate_with_groq(messages)
        return result
    
    def categorize_content(self, text: str) -> str:
        """Determine the subject category of the content.
        
        Args:
            text (str): The text content to categorize.
        
        Returns:
            str: The category name.
        """
        messages = [
            {"role": "system", "content": "Determine the main subject category (e.g., 'History', 'Science', 'Math'). Return only the category name."},
            {"role": "user", "content": text}
        ]
        result = self.generate_with_groq(messages)
        print(result)
        return result

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
            Focus on key concepts: {', '.join(key_concepts)}. 
            Return as JSON array with fields: question, answer, difficulty (easy/medium/hard)"""},
            {"role": "user", "content": summary}
        ]
        
        response = self.generate_with_groq(messages)
        print(response)
        try:
            qa_pairs = json.loads(response)
        except json.JSONDecodeError:
            return []

        flash_cards = []
        try:
            for qa in qa_pairs:
                translated_q = self.translate_content(qa['question'])
                translated_a = self.translate_content(qa['answer'])

                card = FlashCard(
                    prompt=translated_q,
                    answer=translated_a,
                    category=category,
                    difficulty=qa.get('difficulty', 'medium')
                )
                flash_cards.append(card)
        except Exception as e:
            print(f"Error while creating flashcards: {e}")
            return []
        return flash_cards