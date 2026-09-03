"""
exceptions.py
--------------
Shared exception hierarchy for the Vocabulary Learning App.

Every module-specific error inherits (directly or indirectly) from
VocabAppError, so calling code can catch app-level failures with one
except clause when it doesn't care which module raised them, or catch
a specific subclass when it does.

This file only defines the *general-purpose* / cross-cutting errors.
Module-specific error families (e.g. file storage's DataLoadError,
the quiz system's NoQuizDataError) are defined inside their own module
and simply inherit from VocabAppError once this file is importable —
see utils/file_manager.py and services/quiz_generator.py, both of
which already do this automatically.
"""


class VocabAppError(Exception):
    """Base class for every custom exception in this app."""


# ---- Input validation (regex / validators) ---------------------------------
class EmptyInputError(VocabAppError):
    """Raised when the user submits blank input where a word was expected."""


class InvalidWordError(VocabAppError):
    """Raised when input fails validation (numbers, symbols, etc.)."""


# ---- Dictionary lookups (DictionaryClient) ----------------------------------
class WordNotFoundError(VocabAppError):
    """Raised when the dictionary API has no entry for the requested word."""


class APIError(VocabAppError):
    """Raised when an external API call fails (network error, bad response, timeout)."""


# ---- AI content generation (Gemini: explanations, examples, memory tricks) --
class AIGenerationError(VocabAppError):
    """Raised when AI-generated content can't be produced (offline, bad response, etc.)."""
