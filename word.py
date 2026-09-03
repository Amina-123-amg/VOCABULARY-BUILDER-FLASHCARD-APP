"""
models/word.py
================
Owner: Ayobami Omotosho (OOP / Data Model Developer)

Defines the Word class: represents a single vocabulary word and everything
looked up about it (definition, phonetics, examples, synonyms, antonyms).

This class is intentionally storage/UI agnostic — it doesn't know about
Streamlit, files, or the API used to fetch word data. Other team members
build on top of it (e.g. Flashcard.from_word(), search/lookup features,
Streamlit rendering, JSON persistence).
"""

import json


class Word:
    """Represents a single vocabulary word and its dictionary data."""

    def __init__(self, word, definition="", phonetics="", examples=None,
                 synonyms=None, antonyms=None):
        """
        Args:
            word (str): The word itself, e.g. "ephemeral".
            definition (str): The primary definition/meaning of the word.
            phonetics (str): Pronunciation guide, e.g. "/ɪˈfɛm(ə)rəl/".
            examples (list[str]): Example sentences using the word.
            synonyms (list[str]): Words with similar meaning.
            antonyms (list[str]): Words with opposite meaning.
        """
        if not word or not str(word).strip():
            raise ValueError("Word must have a non-empty 'word' value.")

        self.word = str(word).strip().lower()
        self.definition = definition or ""
        self.phonetics = phonetics or ""
        self.examples = list(examples) if examples else []
        self.synonyms = list(synonyms) if synonyms else []
        self.antonyms = list(antonyms) if antonyms else []

    # ----- Convenience methods for other team members to build on -----

    def add_example(self, sentence):
        """Add an example sentence, ignoring empty/duplicate values."""
        if sentence and sentence not in self.examples:
            self.examples.append(sentence)

    def add_synonym(self, synonym):
        """Add a synonym, ignoring empty/duplicate values."""
        if synonym and synonym not in self.synonyms:
            self.synonyms.append(synonym)

    def add_antonym(self, antonym):
        """Add an antonym, ignoring empty/duplicate values."""
        if antonym and antonym not in self.antonyms:
            self.antonyms.append(antonym)

    def has_definition(self):
        """True if this word has a usable definition."""
        return bool(self.definition.strip())

    # ----- Serialization (JSON / file storage) -----

    def to_dict(self):
        """Convert this Word into a plain dict, ready for json.dump()."""
        return {
            "word": self.word,
            "definition": self.definition,
            "phonetics": self.phonetics,
            "examples": self.examples,
            "synonyms": self.synonyms,
            "antonyms": self.antonyms,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Word from a dict (e.g. loaded from JSON). Unknown keys
        are ignored so old/extra fields in saved data won't break this."""
        allowed = {"word", "definition", "phonetics", "examples", "synonyms", "antonyms"}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)

    def to_json(self):
        """Serialize this Word to a JSON string."""
        return json.dumps(self.to_dict(), indent=4)

    @classmethod
    def from_json(cls, json_str):
        """Build a Word from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    # ----- Dunder methods -----

    def __eq__(self, other):
        if not isinstance(other, Word):
            return NotImplemented
        return self.word == other.word

    def __hash__(self):
        return hash(self.word)

    def __repr__(self):
        return f"Word(word={self.word!r}, definition={self.definition!r})"

    def __str__(self):
        return f"{self.word} — {self.definition}" if self.definition else self.word


if __name__ == "__main__":
    # Small self-test so this file can be run directly to sanity-check it.
    w = Word(
        word="ephemeral",
        definition="Lasting for a very short time.",
        phonetics="/ɪˈfɛm(ə)rəl/",
        examples=["Fame in showbiz can be ephemeral."],
        synonyms=["fleeting", "transient"],
        antonyms=["permanent"],
    )
    print(w)
    print(w.to_json())

    # Round-trip through JSON to prove storage compatibility.
    restored = Word.from_json(w.to_json())
    assert restored == w
    print("Round-trip OK:", restored)
