"""
services/quiz_generator.py
---------------------------
The vocabulary quiz system. This module does NOT talk to Gemini (or any
AI) directly — that's the AI content generator's job. This module
*receives* already-generated question data, then owns everything that
happens with it: displaying questions, collecting answers, scoring,
randomizing order, handling missing/bad data, and saving the result
through the File Manager.

Expected input contract (what the AI/Gemini module should hand us) —
a list of dicts, one per question:

    {
        "word": "magnificent",                              # optional
        "question": "What does \"magnificent\" mean?",
        "correct_answer": "Very beautiful or impressive",
        "distractors": ["Very small", "Very angry", "Very old"]
    }

Aliases are accepted too, in case the upstream field names differ:
"answer"/"correct" for correct_answer, and "choices"/"wrong_answers"/
"options" for distractors (the "options" alias must NOT include the
correct answer — same rule as "distractors").

Usage from the rest of the app:

    from services.quiz_generator import run_quiz

    summary = run_quiz(raw_questions_from_gemini, num_questions=10)
    # summary = {"score": 8, "total": 10, "percent": 80.0, "missed_words": [...]}
"""

import random
import string
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
# Same pattern as utils/file_manager.py: slot into the team's shared
# exception hierarchy if it exists, otherwise fall back to a local base.
try:
    from exceptions import VocabAppError as _BaseError
except ImportError:
    class _BaseError(Exception):
        """Fallback base error used when no shared exceptions module exists."""


class QuizError(_BaseError):
    """Base class for all quiz-system errors."""


class NoQuizDataError(QuizError):
    """Raised when there are no usable quiz questions to run a session with."""


class InvalidQuestionDataError(QuizError):
    """Raised when a single raw question item is missing required fields."""


# ---------------------------------------------------------------------------
# Storage hookup (File Manager)
# ---------------------------------------------------------------------------
try:
    from utils.file_manager import record_quiz_score
except ImportError:
    def record_quiz_score(entry):
        """Fallback used only if utils.file_manager isn't on the path yet."""
        print(f"⚠️  utils.file_manager not found — quiz score wasn't saved: {entry}")


DEFAULT_NUM_QUESTIONS = 10


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class QuizQuestion:
    """One ready-to-display question: answer order has already been shuffled."""
    question_text: str
    options: Dict[str, str]   # e.g. {"A": "Very small", "B": "Very beautiful...", ...}
    correct_letter: str
    word: str = ""


# ---------------------------------------------------------------------------
# QuizGenerator: turns raw AI question data into QuizQuestion objects
# ---------------------------------------------------------------------------
class QuizGenerator:
    """Builds a randomized quiz from raw question data received from the AI module."""

    def __init__(self):
        self.questions: List[QuizQuestion] = []

    def load_questions(self, raw_questions: Optional[List[dict]]) -> List[QuizQuestion]:
        """
        Validate and convert raw question dicts into QuizQuestion objects.

        - raw_questions missing/empty -> NoQuizDataError (quiz data unavailable).
        - An individual malformed item is skipped with a warning, not fatal.
        - If every item turns out malformed -> NoQuizDataError.
        """
        if not raw_questions:
            raise NoQuizDataError(
                "No quiz questions were received. The AI question generator "
                "may be offline or hasn't produced any questions yet."
            )

        questions, skipped = [], 0
        for raw in raw_questions:
            try:
                questions.append(self._build_question(raw))
            except InvalidQuestionDataError as e:
                skipped += 1
                print(f"⚠️  Skipping a quiz question: {e}")

        if not questions:
            raise NoQuizDataError(
                f"None of the {skipped} received quiz question(s) were usable."
            )

        self.questions = questions
        return self.questions

    def get_quiz(self, num_questions: int = DEFAULT_NUM_QUESTIONS) -> List[QuizQuestion]:
        """Return a randomly selected AND randomly ordered subset of loaded questions."""
        if not self.questions:
            raise NoQuizDataError("No quiz questions have been loaded yet.")
        k = min(max(1, num_questions), len(self.questions))
        return random.sample(self.questions, k)  # picks + orders randomly in one step

    # ---- internal ----------------------------------------------------
    def _build_question(self, raw: dict) -> QuizQuestion:
        word = raw.get("word", "")
        question_text = raw.get("question") or raw.get("prompt")
        correct = raw.get("correct_answer") or raw.get("answer") or raw.get("correct")
        distractors = (
            raw.get("distractors")
            or raw.get("choices")
            or raw.get("wrong_answers")
            or raw.get("options")
        )

        if not question_text or not correct or not distractors:
            raise InvalidQuestionDataError(
                f"Question for '{word or 'unknown word'}' is missing a question, "
                "correct answer, or distractor list."
            )
        if not isinstance(distractors, list) or len(distractors) == 0:
            raise InvalidQuestionDataError(
                f"Distractors for '{word or 'unknown word'}' must be a non-empty list."
            )

        options_list = list(distractors) + [correct]
        random.shuffle(options_list)  # randomize answer order

        letters = list(string.ascii_uppercase[: len(options_list)])
        options = dict(zip(letters, options_list))
        correct_letter = next(letter for letter, text in options.items() if text == correct)

        return QuizQuestion(
            question_text=question_text,
            options=options,
            correct_letter=correct_letter,
            word=word,
        )


# ---------------------------------------------------------------------------
# QuizSession: displays questions, collects answers, scores, saves
# ---------------------------------------------------------------------------
class QuizSession:
    """Runs one interactive quiz over the console and tracks the score."""

    def __init__(self, questions: List[QuizQuestion]):
        if not questions:
            raise NoQuizDataError("Can't start a quiz session with zero questions.")
        self.questions = questions
        self.correct_count = 0
        self.missed_words: List[str] = []

    def run(self) -> dict:
        total = len(self.questions)
        for i, question in enumerate(self.questions, start=1):
            self._display_question(i, total, question)
            answer = self._get_user_answer(question)

            if answer == question.correct_letter:
                self.correct_count += 1
                print("✅ Correct!\n")
            else:
                correct_text = question.options[question.correct_letter]
                print(f"❌ Not quite — correct answer was {question.correct_letter}. {correct_text}\n")
                if question.word:
                    self.missed_words.append(question.word)

            if i < total:
                input("[Next] Press Enter to continue... ")

        return self._final_summary()

    def save_score(self, summary: dict) -> None:
        try:
            record_quiz_score(summary)
        except Exception as e:
            print(f"⚠️  Couldn't save your quiz score: {e}")

    # ---- internal ----------------------------------------------------
    def _display_question(self, index, total, question: QuizQuestion):
        print(f"\nQuestion {index}/{total}")
        print()
        print(question.question_text)
        print()
        for letter in sorted(question.options):
            print(f"{letter}. {question.options[letter]}")

    def _get_user_answer(self, question: QuizQuestion) -> str:
        valid_letters = set(question.options.keys())
        while True:
            raw = input("\nYour answer: ").strip().upper()
            if raw in valid_letters:
                return raw
            match = next((l for l, text in question.options.items() if text.upper() == raw), None)
            if match:
                return match
            print(f"Please enter one of: {', '.join(sorted(valid_letters))}")

    def _final_summary(self) -> dict:
        total = len(self.questions)
        percent = round((self.correct_count / total) * 100, 1) if total else 0.0
        print(f"\n🏁 Final score: {self.correct_count}/{total} ({percent}%)")
        return {
            "score": self.correct_count,
            "total": total,
            "percent": percent,
            "missed_words": self.missed_words,
        }


# ---------------------------------------------------------------------------
# One-call entry point for the rest of the app
# ---------------------------------------------------------------------------
def run_quiz(raw_questions: Optional[List[dict]], num_questions: int = DEFAULT_NUM_QUESTIONS):
    """
    Build, run, and save a full quiz session in one call.

        from services.quiz_generator import run_quiz
        summary = run_quiz(raw_questions_from_gemini, num_questions=10)

    Returns the score summary dict, or None if the quiz couldn't run
    (e.g. no quiz data was available).
    """
    generator = QuizGenerator()
    try:
        generator.load_questions(raw_questions)
    except NoQuizDataError as e:
        print(f"❌ Can't start the quiz: {e}")
        return None

    questions = generator.get_quiz(num_questions)
    session = QuizSession(questions)
    summary = session.run()
    session.save_score(summary)
    return summary
