from datetime import date, timedelta
from typing import Any, Optional

class SpacedRepetitionService:
    INTERVAL_MAP = {"again": 0, "hard": 1, "good": 3, "easy": 7}

    @staticmethod
    def calculate_next_review(rating: str, current_date: Optional[date] = None):
        rating = rating.lower().strip()
        if rating not in SpacedRepetitionService.INTERVAL_MAP:
            raise ValueError("Rating must be again, hard, good, or easy.")
        base = current_date or date.today()
        days = SpacedRepetitionService.INTERVAL_MAP[rating]
        return {"interval": days, "next_review": (base + timedelta(days=days)).isoformat()}

    @staticmethod
    def get_due_cards(flashcards, current_date: Optional[date] = None):
        today = current_date or date.today()
        due = []
        for card in flashcards:
            due_value = card.get("due_date") if isinstance(card, dict) else getattr(card, "due_date", None)
            try:
                if not due_value or date.fromisoformat(due_value) <= today:
                    due.append(card)
            except ValueError:
                due.append(card)
        return due

    @staticmethod
    def update_review(flashcard: Any, rating: str):
        schedule = SpacedRepetitionService.calculate_next_review(rating)
        if isinstance(flashcard, dict):
            flashcard["interval"] = schedule["interval"]
            flashcard["due_date"] = schedule["next_review"]
            flashcard["repetitions"] = flashcard.get("repetitions", 0) + (1 if rating != "again" else 0)
            flashcard["last_reviewed"] = date.today().isoformat()
        else:
            flashcard.interval = schedule["interval"]
            flashcard.due_date = schedule["next_review"]
            flashcard.repetitions += 1 if rating != "again" else 0
            flashcard.last_reviewed = date.today().isoformat()
        return flashcard
