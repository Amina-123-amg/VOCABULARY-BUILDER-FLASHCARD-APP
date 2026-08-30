"""
gemini_client.py

Gemini AI helper for the Vocabulary Builder application.

This module generates:
- simple word explanations
- simple example sentences
- memory tricks / mnemonics
- multiple-choice vocabulary quizzes

Setup:
    pip install -U google-genai

Set your API key as an environment variable:
    GEMINI_API_KEY=your_api_key_here

Do NOT put the real API key directly in this file.
"""

import json
import os
import re
from typing import Any, Dict, List

from google import genai


class GeminiError(Exception):
    """Raised when Gemini cannot generate the requested content."""
    pass


class GeminiClient:
    """Handles all communication between the app and Gemini AI."""

    MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str | None = None):
        # Use the supplied key first, otherwise use GEMINI_API_KEY.
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise GeminiError(
                "Gemini API key not found. Set the GEMINI_API_KEY environment variable."
            )

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:
            raise GeminiError(f"Could not connect to Gemini: {exc}") from exc

    @staticmethod
    def _validate_word(word: str) -> str:
        """Validate and clean the word before sending it to Gemini."""
        if not word or not word.strip():
            raise ValueError("Please provide a word.")

        word = word.strip()

        # Vocabulary words may contain letters, numbers, apostrophes,
        # hyphens and spaces (for words such as "mother-in-law").
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9' -]*", word):
            raise ValueError("Please enter a valid word.")

        return word

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove unnecessary formatting and punctuation from AI text."""
        text = str(text).strip()

        # Remove common Markdown formatting.
        text = re.sub(r"[*_`#]+", "", text)

        # Remove repeated spaces.
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _generate_text(self, prompt: str) -> str:
        """Send a normal text-generation request to Gemini."""
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
            )

            text = getattr(response, "text", None)

            if not text:
                raise GeminiError("Gemini returned an empty response.")

            return self._clean_text(text)

        except GeminiError:
            raise
        except Exception as exc:
            raise GeminiError(f"Gemini API request failed: {exc}") from exc

    def generate_explanation(self, word: str) -> str:
        """Generate a simple, beginner-friendly explanation."""
        word = self._validate_word(word)

        prompt = f"""
You are a friendly vocabulary teacher.

Explain the word "{word}" to a beginner.

Rules:
- Give one short and simple explanation.
- Use everyday English.
- Do not use difficult words to explain the word.
- Do not include headings, bullet points, or Markdown.
- Give only the explanation.
"""

        return self._generate_text(prompt)

    def generate_example(self, word: str) -> str:
        """Generate one simple example sentence."""
        word = self._validate_word(word)

        prompt = f"""
You are a beginner-friendly English teacher.

Write ONE short, natural example sentence using the word "{word}".

Rules:
- The sentence must clearly show the meaning of the word.
- Use simple everyday English.
- Do not add an explanation.
- Do not use quotation marks or Markdown.
- Give only the sentence.
"""

        return self._generate_text(prompt)

    def generate_memory_trick(self, word: str) -> str:
        """Generate a simple mnemonic or memory trick."""
        word = self._validate_word(word)

        prompt = f"""
Create a simple memory trick for the vocabulary word "{word}".

Rules:
- Make it easy for a beginner to remember.
- Use a short association, word connection, or mini-story.
- Keep it to one or two short sentences.
- Do not use Markdown or headings.
- Give only the memory trick.
"""

        return self._generate_text(prompt)

    def generate_quiz(self, word: str) -> Dict[str, Any]:
        """
        Generate one multiple-choice quiz question.

        Returns a dictionary in this format:
        {
            "question": "...",
            "options": ["...", "...", "...", "..."],
            "correct_answer": "..."
        }
        """
        word = self._validate_word(word)

        schema = {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "One simple vocabulary question about the word."
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exactly four possible answers."
                },
                "correct_answer": {
                    "type": "string",
                    "description": "The exact text of the correct option."
                },
            },
            "required": ["question", "options", "correct_answer"],
        }

        prompt = f"""
Create one beginner-friendly multiple-choice vocabulary quiz for the word "{word}".

Rules:
- Ask one clear question that tests the meaning or correct use of the word.
- Give exactly four answer choices.
- Only one choice must be correct.
- Keep all choices short and simple.
- The correct_answer must exactly match one of the options.
- Return only the requested JSON structure.
"""

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )

            text = getattr(response, "text", None)

            if not text:
                raise GeminiError("Gemini returned an empty quiz response.")

            quiz = json.loads(text)

            # Basic validation so the rest of the application receives
            # predictable data.
            question = self._clean_text(quiz.get("question", ""))
            options = quiz.get("options", [])
            correct_answer = self._clean_text(
                quiz.get("correct_answer", "")
            )

            if not question:
                raise GeminiError("Quiz question was empty.")

            if not isinstance(options, list) or len(options) != 4:
                raise GeminiError("Gemini did not return exactly four quiz options.")

            options = [self._clean_text(option) for option in options]

            if correct_answer not in options:
                raise GeminiError(
                    "Gemini returned a correct answer that is not one of the options."
                )

            return {
                "question": question,
                "options": options,
                "correct_answer": correct_answer,
            }

        except GeminiError:
            raise
        except json.JSONDecodeError as exc:
            raise GeminiError("Gemini returned quiz data that was not valid JSON.") from exc
        except Exception as exc:
            raise GeminiError(f"Gemini quiz request failed: {exc}") from exc


# Simple test:
# Run this file directly after setting GEMINI_API_KEY to test the connection.
if __name__ == "__main__":
    try:
        client = GeminiClient()

        word = input("Enter a word: ").strip()

        print("\nExplanation:")
        print(client.generate_explanation(word))

        print("\nExample:")
        print(client.generate_example(word))

        print("\nMemory trick:")
        print(client.generate_memory_trick(word))

        print("\nQuiz:")
        print(json.dumps(client.generate_quiz(word), indent=2))

    except (GeminiError, ValueError) as exc:
        print(f"\nError: {exc}")

        
