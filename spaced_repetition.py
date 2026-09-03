from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

class SpacedRepetitionService:
    """
    Handles spaced repetition scheduling logic for flashcard reviews.
    """

    INTERVAL_MAP = {
        "again": 0,  # Due today / immediately
        "hard": 1,   # Due in 1 day
        "good": 3,   # Due in 3 days
        "easy": 7    # Due in 7 days
    }

    @staticmethod
    def calculate_next_review(difficulty: str, current_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Calculates the next review date and interval based on user rating.
        
        :param difficulty: 'again', 'hard', 'good', or 'easy'
        :param current_date: Optional base date (defaults to today)
        :return: Dictionary containing 'next_review' (ISO date string) and 'interval' (int days)
        """
        rating = difficulty.lower().strip()
        if rating not in SpacedRepetitionService.INTERVAL_MAP:
            raise ValueError(f"Invalid difficulty rating '{difficulty}'. Choose from: again, hard, good, easy.")

        base_date = current_date if current_date else date.today()
        days_to_add = SpacedRepetitionService.INTERVAL_MAP[rating]
        
        next_review_date = base_date + timedelta(days=days_to_add)

        return {
            "interval": days_to_add,
            "next_review": next_review_date.isoformat()
        }

    @staticmethod
    def get_due_cards(flashcards: List[Any], current_date: Optional[date] = None) -> List[Any]:
        """
        Filters a list of Flashcard objects or dicts to return only those due for review.
        
        :param flashcards: List of Flashcard objects or dictionary representations
        :param current_date: Optional comparison date (defaults to today)
        :return: List of due flashcards
        """
        today = current_date if current_date else date.today()
        due_cards = []

        for card in flashcards:
            # Extract next_review whether card is a dict or a class instance
            if isinstance(card, dict):
                next_review_str = card.get("next_review")
            else:
                next_review_str = getattr(card, "next_review", None)

            if not next_review_str:
                # If no date is set, consider it due for review immediately
                due_cards.append(card)
                continue

            try:
                review_date = datetime.strptime(next_review_str, "%Y-%m-%d").date()
                if review_date <= today:
                    due_cards.append(card)
            except ValueError:
                # Fallback in case of malformed date strings
                due_cards.append(card)

        return due_cards

    @staticmethod
    def update_review(flashcard: Any, rating: str, file_manager: Optional[Any] = None) -> Any:
        """
        Updates the flashcard's review schedule and optionally saves it via FileManager.
        
        :param flashcard: Flashcard object or dictionary
        :param rating: User's review rating ('again', 'hard', 'good', 'easy')
        :param file_manager: Optional instance of FileManager to persist data
        :return: Updated flashcard instance or dict
        """
        schedule = SpacedRepetitionService.calculate_next_review(rating)

        if isinstance(flashcard, dict):
            flashcard["interval"] = schedule["interval"]
            flashcard["next_review"] = schedule["next_review"]
        else:
            setattr(flashcard, "interval", schedule["interval"])
            setattr(flashcard, "next_review", schedule["next_review"])

        # If file_manager reference is provided, execute save operation
        if file_manager and hasattr(file_manager, "save_data"):
            file_manager.save_data()

        return flashcard
