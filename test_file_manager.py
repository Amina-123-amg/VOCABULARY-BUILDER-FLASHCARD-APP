"""
Quick smoke tests for utils/file_manager.py.
Run with: python3 tests/test_file_manager.py
"""
import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import file_manager as fm

PASS = "✅"
FAIL = "❌"
failures = []


def check(label, condition):
    print(f"{PASS if condition else FAIL} {label}")
    if not condition:
        failures.append(label)


def main():
    tmp_dir = tempfile.mkdtemp(prefix="vocab_fm_test_")
    fm.DATA_DIR = tmp_dir  # redirect the module at a scratch dir for this test run
    print(f"Using scratch data dir: {tmp_dir}\n")

    # 1. Missing file -> default, no crash
    words = fm.load_saved_words()
    check("missing saved_words.json returns {} instead of crashing", words == {})

    # 2. Save + load round trip
    fm.save_word("ephemeral", {"definition": "lasting a very short time", "phonetic": "/əˈfɛm(ə)rəl/"})
    words = fm.load_saved_words()
    check("save_word() persists and load_saved_words() reads it back",
          words.get("ephemeral", {}).get("definition") == "lasting a very short time")

    # 3. Adding a second word doesn't erase the first
    fm.save_word("lucid", {"definition": "clear and easy to understand"})
    words = fm.load_saved_words()
    check("adding a new word keeps the previous word intact",
          "ephemeral" in words and "lucid" in words)

    # 4. Partial update merges instead of overwriting the whole record
    fm.save_word("ephemeral", {"synonyms": ["fleeting", "transient"]})
    words = fm.load_saved_words()
    rec = words["ephemeral"]
    check("partial update merges fields instead of wiping the record",
          rec.get("definition") == "lasting a very short time" and rec.get("synonyms") == ["fleeting", "transient"])

    # 5. Flashcards + progress are independent stores
    fm.save_flashcard("ephemeral", {"front": "ephemeral", "back": "lasting a very short time", "interval": 1})
    fm.update_progress("ephemeral", {"repetitions": 1, "ease_factor": 2.5, "due_date": "2026-08-30"})
    check("flashcards.json created independently", "ephemeral" in fm.load_flashcards())
    check("progress.json created independently", "ephemeral" in fm.load_progress())

    # 6. Quiz scores append rather than overwrite
    fm.record_quiz_score({"score": 4, "total": 5, "percent": 80.0})
    fm.record_quiz_score({"score": 5, "total": 5, "percent": 100.0})
    scores = fm.load_quiz_scores()
    check("quiz scores accumulate as a list (2 entries)", len(scores) == 2)
    check("quiz score entries get an auto timestamp", "timestamp" in scores[0])

    # 7. Corrupted JSON is quarantined, not deleted, and app keeps running
    bad_path = os.path.join(tmp_dir, "flashcards.json")
    with open(bad_path, "w") as f:
        f.write("{ this is not : valid json ,,,")
    recovered = fm.load_flashcards()
    check("corrupted flashcards.json recovers to {} instead of raising", recovered == {})
    backups = [f for f in os.listdir(tmp_dir) if "flashcards.json.corrupted-" in f]
    check("corrupted file was backed up (not deleted)", len(backups) == 1)

    # 8. After recovery, saving still works normally
    fm.save_flashcard("lucid", {"front": "lucid", "back": "clear and easy to understand"})
    check("file_manager still works normally after a corruption recovery",
          "lucid" in fm.load_flashcards())

    # 9. delete_entry removes only the targeted record
    fm.remove_word("lucid")
    remaining = fm.load_saved_words()
    check("remove_word deletes only the targeted word",
          "lucid" not in remaining and "ephemeral" in remaining)

    # 10. save_data keeps a .bak of the previous version
    bak_exists = os.path.exists(os.path.join(tmp_dir, "saved_words.json.bak"))
    check("a .bak backup of the previous save exists", bak_exists)

    shutil.rmtree(tmp_dir, ignore_errors=True)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: {failures}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
