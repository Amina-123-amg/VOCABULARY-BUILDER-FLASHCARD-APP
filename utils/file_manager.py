"""
utils/file_manager.py
----------------------
All local JSON persistence for the vocabulary app lives here: saved words,
flashcards, quiz scores, and spaced-repetition progress.

Design goals (matching the file-handling spec):
    * save_data() / load_data() / update_data() as the core building blocks.
    * Missing files are treated as "no data yet", not an error.
    * Corrupted JSON is quarantined (renamed, never deleted) instead of
      crashing the app.
    * Saves are atomic and keep a backup of the previous version, so a
      crash mid-write (or a bad update) can never silently delete data.
    * All real I/O failures are raised as specific custom exceptions.
"""

import json
import os
import shutil
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
# If the team already has a shared exceptions.py (e.g. a VocabAppError base
# class), this module will slot into that hierarchy automatically. If not,
# it falls back to its own base exception so it still works standalone.
try:
    from exceptions import VocabAppError as _BaseError
except ImportError:
    class _BaseError(Exception):
        """Fallback base error used when no shared exceptions module exists."""


class FileManagerError(_BaseError):
    """Base class for all errors raised by file_manager."""


class DataLoadError(FileManagerError):
    """Raised when a data file exists but can't be read (permissions, I/O, etc.)."""


class DataSaveError(FileManagerError):
    """Raised when data can't be written to disk."""


class CorruptedDataError(FileManagerError):
    """Raised (in strict mode) when a data file contains invalid JSON."""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")

SAVED_WORDS_FILE = "saved_words.json"
FLASHCARDS_FILE = "flashcards.json"
QUIZ_SCORES_FILE = "quiz_scores.json"
PROGRESS_FILE = "progress.json"


def _ensure_data_dir():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except OSError as e:
        raise DataSaveError(f"Could not create data directory '{DATA_DIR}': {e}") from e


def _path_for(filename):
    return os.path.join(DATA_DIR, filename)


def _quarantine_corrupted_file(path):
    """Rename (never delete) a corrupted file so the bad data isn't lost."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{path}.corrupted-{timestamp}.bak"
    try:
        shutil.move(path, backup_path)
        return backup_path
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Core: load_data / save_data / update_data / append_data / delete_entry
# ---------------------------------------------------------------------------
def load_data(filename, default=None, strict=False):
    """
    Load JSON data from `filename` inside data/.

    - Missing file            -> returns `default`.
    - Empty file               -> returns `default` (not treated as corrupt).
    - Corrupted/invalid JSON  -> if strict=False (default): the bad file is
      quarantined (renamed with a timestamp, never deleted) and `default`
      is returned so the app keeps running. If strict=True: raises
      CorruptedDataError instead.
    - Real read errors (permissions, disk issues) -> raises DataLoadError.
    """
    if default is None:
        default = {}

    _ensure_data_dir()
    path = _path_for(filename)

    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        raise DataLoadError(f"Could not read '{filename}': {e}") from e

    if not raw.strip():
        return default

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        if strict:
            raise CorruptedDataError(f"'{filename}' contains invalid JSON: {e}") from e
        backup = _quarantine_corrupted_file(path)
        note = f" (backed up to {os.path.basename(backup)})" if backup else ""
        print(f"⚠️  '{filename}' had invalid JSON and was reset{note}.")
        return default


def save_data(filename, data):
    """
    Save `data` to `filename` inside data/.

    Writes are atomic (write to a .tmp file, then rename over the
    original) and the previous version is copied to a .bak file first,
    so a crash mid-write — or an accidental overwrite — can't destroy
    existing data.
    """
    _ensure_data_dir()
    path = _path_for(filename)
    tmp_path = f"{path}.tmp"
    backup_path = f"{path}.bak"

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (OSError, TypeError) as e:
        raise DataSaveError(f"Could not write '{filename}': {e}") from e

    if os.path.exists(path):
        try:
            shutil.copyfile(path, backup_path)
        except OSError:
            pass  # backup is best-effort; must not block the actual save

    try:
        os.replace(tmp_path, path)
    except OSError as e:
        raise DataSaveError(f"Could not finalize save for '{filename}': {e}") from e


def update_data(filename, key, value):
    """
    Upsert a single record inside a dict-shaped JSON file (saved_words,
    flashcards, progress) without touching any other record already saved.

    If a record already exists for `key` and both the old and new values
    are dicts, they are merged (so a partial update doesn't erase fields
    the caller didn't mention). Otherwise the value is replaced outright.
    """
    data = load_data(filename, {})
    if not isinstance(data, dict):
        raise FileManagerError(
            f"'{filename}' does not hold key/value records; use append_data() instead."
        )

    existing = data.get(key)
    if isinstance(existing, dict) and isinstance(value, dict):
        data[key] = {**existing, **value}
    else:
        data[key] = value

    save_data(filename, data)
    return data[key]


def append_data(filename, record):
    """
    Append one record to a list-shaped JSON file (quiz_scores), keeping
    every entry already saved. Stamps a UTC timestamp on dict records
    that don't already have one.
    """
    data = load_data(filename, [])
    if not isinstance(data, list):
        raise FileManagerError(
            f"'{filename}' does not hold a list of records; use update_data() instead."
        )
    if isinstance(record, dict):
        record.setdefault("timestamp", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    data.append(record)
    save_data(filename, data)
    return data


def delete_entry(filename, key):
    """Remove a single record from a dict-shaped JSON file, if present."""
    data = load_data(filename, {})
    if not isinstance(data, dict):
        raise FileManagerError(f"'{filename}' does not hold key/value records.")
    removed = data.pop(key, None)
    if removed is not None:
        save_data(filename, data)
    return removed


# ---------------------------------------------------------------------------
# Domain-specific convenience wrappers
# (what the rest of the team's classes will actually call)
# ---------------------------------------------------------------------------

# ---- Saved words -----------------------------------------------------------
def load_saved_words():
    """Return {word: word_record} for every saved word."""
    return load_data(SAVED_WORDS_FILE, {})


def save_word(word_key, word_data):
    """Add or update one saved word (e.g. word_key='ephemeral')."""
    return update_data(SAVED_WORDS_FILE, word_key.lower(), word_data)


def remove_word(word_key):
    return delete_entry(SAVED_WORDS_FILE, word_key.lower())


# ---- Flashcards -------------------------------------------------------------
def load_flashcards():
    """Return {word: flashcard_record} for every flashcard."""
    return load_data(FLASHCARDS_FILE, {})


def save_flashcard(word_key, flashcard_data):
    return update_data(FLASHCARDS_FILE, word_key.lower(), flashcard_data)


def remove_flashcard(word_key):
    return delete_entry(FLASHCARDS_FILE, word_key.lower())


# ---- Quiz scores (append-only history) --------------------------------------
def load_quiz_scores():
    """Return a list of every past quiz attempt, oldest first."""
    return load_data(QUIZ_SCORES_FILE, [])


def record_quiz_score(score_entry):
    """
    Append one quiz attempt, e.g.:
        record_quiz_score({"score": 4, "total": 5, "percent": 80.0})
    """
    return append_data(QUIZ_SCORES_FILE, score_entry)


# ---- Review / spaced-repetition progress -------------------------------------
def load_progress():
    """Return {word: progress_record} — review streaks, due dates, etc."""
    return load_data(PROGRESS_FILE, {})


def update_progress(word_key, progress_data):
    return update_data(PROGRESS_FILE, word_key.lower(), progress_data)
