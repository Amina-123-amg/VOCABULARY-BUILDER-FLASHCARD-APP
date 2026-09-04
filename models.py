from dataclasses import dataclass, field, asdict, fields
from datetime import date
from typing import List, Optional

try:
    from exceptions import VocabAppError as _BaseError
except ImportError:
    class _BaseError(Exception):
        """Fallback base error used when no shared exceptions module exists."""


class ModelError(_BaseError):
    """Base class for errors raised while building or parsing model objects."""


class InvalidWordDataError(ModelError):
    """Raised when raw dictionary API data can't be parsed into a Word."""


def _dedupe(items: List[str]) -> List[str]:
    """Remove duplicates (case-insensitive) while preserving order."""
    seen, out = set(), []
    for item in items:
        if item and item.lower() not in seen:
            seen.add(item.lower())
            out.append(item)
    return out


def _filtered(cls, data: dict) -> dict:
    """Keep only the keys that `cls` (a dataclass) actually has fields for."""
    valid = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in valid}


@dataclass
class Definition:
    """One meaning of a word."""
    part_of_speech: str = ""
    definition: str = ""
    example: str = ""
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Definition":
        return cls(**_filtered(cls, data))


@dataclass
class Word:
    """A looked-up word: one or more Definitions, plus optional AI extras."""
    text: str
    phonetic: str = ""
    definitions: List[Definition] = field(default_factory=list)
    simple_explanation: str = ""
    ai_examples: List[str] = field(default_factory=list)
    memory_trick: str = ""

    @classmethod
    def from_api_response(cls, word_text: str, raw_data: list) -> "Word":
        """Build a Word from dictionaryapi.dev's raw JSON response."""
        if not raw_data or not isinstance(raw_data, list):
            raise InvalidWordDataError(
                f"Received no usable dictionary data for '{word_text}'."
            )

        entry = raw_data[0]

        phonetic = entry.get("phonetic", "")
        if not phonetic:
            for p in entry.get("phonetics", []):
                if p.get("text"):
                    phonetic = p["text"]
                    break

        definitions = []
        for meaning in entry.get("meanings", []):
            part_of_speech = meaning.get("partOfSpeech", "")
            meaning_synonyms = meaning.get("synonyms", [])
            meaning_antonyms = meaning.get("antonyms", [])

            for d in meaning.get("definitions", []):
                definitions.append(Definition(
                    part_of_speech=part_of_speech,
                    definition=(d.get("definition") or "").strip(),
                    example=(d.get("example") or "").strip(),
                    synonyms=_dedupe(
                        d.get("synonyms", []) + meaning_synonyms
                    ),
                    antonyms=_dedupe(
                        d.get("antonyms", []) + meaning_antonyms
                    ),
                ))

        if not definitions:
            raise InvalidWordDataError(
                f"Dictionary data for '{word_text}' had no usable definitions."
            )

        return cls(
            text=word_text,
            phonetic=phonetic,
            definitions=definitions
        )

    @property
    def primary_definition(self) -> str:
        return (
            self.definitions[0].definition
            if self.definitions
            else "No definition available."
        )

    @property
    def primary_example(self) -> str:
        for d in self.definitions:
            if d.example:
                return d.example
        return ""

    @property
    def part_of_speech(self) -> str:
        return self.definitions[0].part_of_speech if self.definitions else ""

    @property
    def all_synonyms(self) -> List[str]:
        result = []
        for d in self.definitions:
            result.extend(d.synonyms)
        return _dedupe(result)

    @property
    def all_antonyms(self) -> List[str]:
        result = []
        for d in self.definitions:
            result.extend(d.antonyms)
        return _dedupe(result)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Word":
        definitions = [
            d if isinstance(d, Definition) else Definition.from_dict(d)
            for d in data.get("definitions", [])
        ]

        return cls(
            text=data.get("text", ""),
            phonetic=data.get("phonetic", ""),
            definitions=definitions,
            simple_explanation=data.get("simple_explanation", ""),
            ai_examples=list(data.get("ai_examples") or []),
            memory_trick=data.get("memory_trick", ""),
        )


@dataclass
class Flashcard:
    """One spaced-repetition flashcard for a saved word."""
    word: str
    front: str = ""
    back: str = ""
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    due_date: str = field(
        default_factory=lambda: date.today().isoformat()
    )
    last_reviewed: Optional[str] = None

    def is_due(self, today: Optional[date] = None) -> bool:
        today = today or date.today()

        try:
            return date.fromisoformat(self.due_date) <= today
        except (ValueError, TypeError):
            return True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Flashcard":
        return cls(**_filtered(cls, data))
