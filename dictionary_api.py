import requests
from typing import List

from exceptions import APIError, EmptyInputError, WordNotFoundError
from models import Word, clean_text


class DictionaryClient:
    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def lookup(self, word: str) -> Word:
        if not word or not word.strip():
            raise EmptyInputError("No word given to look up.")

        url = f"{self.BASE_URL}{word.strip().lower()}"
        try:
            resp = requests.get(url, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise APIError("Dictionary lookup timed out. Check your connection and try again.")
        except requests.exceptions.ConnectionError:
            raise APIError("Couldn't reach the dictionary service. Check your internet connection.")
        except requests.exceptions.RequestException as exc:
            raise APIError(f"Dictionary request failed: {exc}")

        if resp.status_code == 404:
            raise WordNotFoundError(f"'{word}' was not found in the dictionary.")
        if resp.status_code != 200:
            raise APIError(f"Dictionary service returned an error (status {resp.status_code}).")

        try:
            data = resp.json()
        except ValueError:
            raise APIError("Dictionary service returned a response that couldn't be read.")

        return self._parse(word, data)

    def _parse(self, word: str, data: list) -> Word:
        if not data or not isinstance(data, list):
            raise WordNotFoundError(f"'{word}' was not found in the dictionary.")

        entry = data[0]
        phonetic = entry.get("phonetic") or ""
        if not phonetic:
            for p in entry.get("phonetics", []):
                if p.get("text"):
                    phonetic = p["text"]
                    break

        part_of_speech = ""
        definitions = []
        examples = []
        synonyms = []
        antonyms = []

        for meaning in entry.get("meanings", []):
            if not part_of_speech:
                part_of_speech = meaning.get("partOfSpeech", "")
            synonyms.extend(meaning.get("synonyms", []))
            antonyms.extend(meaning.get("antonyms", []))
            for d in meaning.get("definitions", []):
                if d.get("definition"):
                    definitions.append(clean_text(d["definition"]))
                if d.get("example"):
                    examples.append(clean_text(d["example"]))
                synonyms.extend(d.get("synonyms", []))
                antonyms.extend(d.get("antonyms", []))

        return Word(
            text=word.lower(),
            phonetic=phonetic,
            part_of_speech=part_of_speech,
            definitions=self._dedupe(definitions)[:5],
            examples=self._dedupe(examples)[:5],
            synonyms=self._dedupe(synonyms)[:10],
            antonyms=self._dedupe(antonyms)[:10],
            source="dictionary_api",
        )

    @staticmethod
    def _dedupe(seq: List[str]) -> List[str]:
        seen = set()
        out = []
        for item in seq:
            cleaned = item.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                out.append(cleaned)
        return out
