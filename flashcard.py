"""
models/flashcard.py
=====================
Owner: Ayobami Omotosho (OOP / Data Model Developer)

Defines the Flashcard class: the reviewable unit built from a Word, with
the extra fields needed for spaced repetition (interval, next_review) and
memory aids.

Like Word, this class is storage/UI agnostic. It exposes simple, predictable
methods (to_dict/from_dict, from_word, is_due, schedule_next_review) so the
teammate building the actual SM-2 spaced-repetition engine, and the teammate
building the Streamlit UI, can both use it without needing to know its
internals.
"""

import json
from datetime import datetime, timedelta

try:
    from word import Word
except ImportError:  # allows running this file directly, e.g. `python flashcard.py`
    from word import Word


class Flashcard:
    """Represents a single reviewable flashcard, derived from a Word."""

    def __init__(self, word, definition="", example="", memory_trick="",
                 interval=1, next_review=None):
        """
        Args:
            word (str): The word this flashcard tests, e.g. "ephemeral".
            definition (str): The definition shown on the back of the card.
            example (str): An example sentence shown on the back of the card.
            memory_trick (str): A mnemonic/memory aid for recalling the word.
            interval (int): Days until the card is due again.
            next_review (str): ISO date string (YYYY-MM-DD) of next review.
                                Defaults to today if not given.
        """
        if not word or not str(word).strip():
            raise ValueError("Flashcard must have a non-empty 'word' value.")

        self.word = str(word).strip().lower()
        self.definition = definition or ""
        self.example = example or ""
        self.memory_trick = memory_trick or ""
        self.interval = int(interval) if interval else 1
        self.next_review = next_review or datetime.now().date().isoformat()

    # ----- Construction helpers -----

    @classmethod
    def from_word(cls, word_obj, memory_trick=""):
        """Build a Flashcard directly from a Word instance.

        Args:
            word_obj (Word): The source word.
            memory_trick (str): Optional mnemonic to attach.
        """
        if not isinstance(word_obj, Word):
            raise TypeError("from_word() expects a Word instance.")

        example = word_obj.examples[0] if word_obj.examples else ""
        return cls(
            word=word_obj.word,
            definition=word_obj.definition,
            example=example,
            memory_trick=memory_trick,
        )

    # ----- Review-related helpers (data-level only; the actual SM-2/SRS
    # scoring algorithm is owned by whoever builds the review engine) -----

    def is_due(self, on_date=None):
        """True if this card is due for review on/ before the given date
        (defaults to today)."""
        check_date = on_date or datetime.now().date().isoformat()
        return self.next_review <= check_date

    def schedule_next_review(self, interval_days):
        """Push this card's next_review forward by interval_days from today,
        and update the stored interval. Kept intentionally simple — the
        review engine can call this after computing its own interval."""
        self.interval = int(interval_days)
        self.next_review = (datetime.now().date() + timedelta(days=self.interval)).isoformat()
        return self

    # ----- Serialization (JSON / file storage) -----

    def to_dict(self):
        """Convert this Flashcard into a plain dict, ready for json.dump()."""
        return {
            "word": self.word,
            "definition": self.definition,
            "example": self.example,
            "memory_trick": self.memory_trick,
            "interval": self.interval,
            "next_review": self.next_review,
        }

    @classmethod
    def from_dict(cls, data):
        """Build a Flashcard from a dict (e.g. loaded from JSON). Unknown
        keys are ignored so old/extra saved fields won't break this."""
        allowed = {"word", "definition", "example", "memory_trick", "interval", "next_review"}
        clean = {k: v for k, v in data.items() if k in allowed}
        return cls(**clean)

    def to_json(self):
        """Serialize this Flashcard to a JSON string."""
        return json.dumps(self.to_dict(), indent=4)

    @classmethod
    def from_json(cls, json_str):
        """Build a Flashcard from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    # ----- Dunder methods -----

    def __eq__(self, other):
        if not isinstance(other, Flashcard):
            return NotImplemented
        return self.word == other.word

    def __hash__(self):
        return hash(self.word)

    def __repr__(self):
        return f"Flashcard(word={self.word!r}, next_review={self.next_review!r})"

    def __str__(self):
        return f"[{self.word}] due {self.next_review}"


if __name__ == "__main__":
    # Small self-test so this file can be run directly to sanity-check it.
    w = Word(
        word="resilient",
        definition="Able to recover quickly from difficulties.",
        examples=["The resilient team bounced back after a tough loss."],
        synonyms=["tough", "hardy"],
        antonyms=["fragile"],
    )
    card = Flashcard.from_word(w, memory_trick="Think of a rubber band bouncing back into shape.")
    print(card)
    print(card.to_json())

    # Round-trip through JSON to prove storage compatibility.
    restored = Flashcard.from_dict(card.to_dict())
    assert restored == card
    print("Round-trip OK:", restored)

    # Simulate a review engine scheduling the next review.
    card.schedule_next_review(6)
    print("After scheduling:", card, "| is_due today:", card.is_due())
