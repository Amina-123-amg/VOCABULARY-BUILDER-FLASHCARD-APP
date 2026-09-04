import re
import requests
from models import Word
from exceptions import EmptyInputError, InvalidWordError, WordNotFoundError, APIError

BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"

class DictionaryClient:
    """Fetch English word information from the Free Dictionary API."""

    @staticmethod
    def validate_word(word: str) -> str:
        if not word or not word.strip():
            raise EmptyInputError("Please enter a word.")
        word = re.sub(r"\s+", " ", word.strip())
        if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", word):
            raise InvalidWordError("Please enter a valid English word.")
        return word.lower()

    def get_word(self, word: str) -> Word:
        word = self.validate_word(word)
        try:
            response = requests.get(f"{BASE_URL}/{word}", timeout=30)
        except requests.RequestException as exc:
            raise APIError(f"Could not connect to the dictionary service: {exc}") from exc

        if response.status_code == 404:
            raise WordNotFoundError(f"'{word}' was not found in the dictionary.")
        if response.status_code != 200:
            raise APIError(f"Dictionary service returned HTTP {response.status_code}.")

        try:
            data = response.json()
        except ValueError as exc:
            raise APIError("The dictionary service returned invalid JSON.") from exc

        try:
            return Word.from_api_response(word, data)
        except Exception as exc:
            raise APIError(f"Could not read dictionary data for '{word}': {exc}") from exc
