import os
import json
from typing import List, Dict

from groq import Groq


GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class AnalyzeDocs:
    def __init__(self, target_language="english"):
        self.target_language = target_language
        self.client_groq = Groq(api_key=GROQ_API_KEY)

    def generate_with_groq(self, messages: List[Dict[str, str]]) -> str:
        completion = self.client_groq.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.7,
        )
        return completion.choices[0].message.content
    
    def summarize_text(self, text: str) -> str:
        """Summarize long text into key points."""
        messages = [
            {"role": "system", "content": "Summarize the following text into key points."},
            {"role": "user", "content": text}
        ]
        return self.generate_with_groq(messages)
        
    def generate_qa_pairs(self, summary: str) -> List[Dict[str, str]]:
        """Generate relevant Q&A pairs from the summary."""
        messages = [
            {"role": "system", "content": "Generate 3 relevant question-answer pairs from this text. Return as JSON array with 'question' and 'answer' fields."},
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
        """Translate content to target language."""
        if self.target_language.lower() == "english":
            return content

        messages = [
            {"role": "system", "content": f"Translate the following text to {self.target_language}, maintaining any technical terms appropriate for a school context."},
            {"role": "user", "content": content}
        ]
        return self.generate_with_groq(messages)
    
    def process_document(self, text: str) -> List[Dict[str, str]]:
        """Process entire document through the pipeline."""
        summary = self.summarize_text(text)

        qa_pairs = self.generate_qa_pairs(summary)

        flash_cards = []
        for qa in qa_pairs:
            translated_q = self.translate_content(qa['question'])
            translated_a = self.translate_content(qa['answer'])

            flash_card = {
                "prompt": translated_q,
                "answer": translated_a
            }
            flash_cards.append(flash_card)
        
        return flash_cards