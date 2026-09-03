"""
Smoke tests for services/quiz_generator.py.
Run with: python3 tests/test_quiz_generator.py
"""
import os
import sys
import builtins

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import quiz_generator as qg

PASS, FAIL = "✅", "❌"
failures = []


def check(label, condition):
    print(f"{PASS if condition else FAIL} {label}")
    if not condition:
        failures.append(label)


SAMPLE_RAW = [
    {
        "word": "magnificent",
        "question": 'What does "magnificent" mean?',
        "correct_answer": "Very beautiful or impressive",
        "distractors": ["Very small", "Very angry", "Very old"],
    },
    {
        "word": "lucid",
        "question": 'What does "lucid" mean?',
        "correct_answer": "Clear and easy to understand",
        "distractors": ["Confusing and vague", "Extremely loud", "Very heavy"],
    },
    {
        "word": "ephemeral",
        "question": 'What does "ephemeral" mean?',
        "correct_answer": "Lasting a very short time",
        "distractors": ["Lasting forever", "Very colorful", "Extremely large"],
    },
]


def with_inputs(monkeypatch_queue):
    """Return a fake input() that pops answers off a queue in order."""
    it = iter(monkeypatch_queue)

    def fake_input(prompt=""):
        return next(it)

    return fake_input


def main():
    # 1. Loading valid raw data
    gen = qg.QuizGenerator()
    gen.load_questions(SAMPLE_RAW)
    check("load_questions() builds one QuizQuestion per valid raw item", len(gen.questions) == 3)

    # 2. Structural correctness: correct_letter always points at the right text
    all_correct_mapped = all(
        q.options[q.correct_letter] in (
            "Very beautiful or impressive", "Clear and easy to understand", "Lasting a very short time"
        )
        for q in gen.questions
    )
    check("shuffled options still map correct_letter to the right answer text", all_correct_mapped)

    # 3. Options actually contain all 4 choices (1 correct + 3 distractors)
    check("each question has 4 answer options", all(len(q.options) == 4 for q in gen.questions))

    # 4. Empty / None raw data -> NoQuizDataError (quiz data unavailable)
    try:
        qg.QuizGenerator().load_questions([])
        check("empty raw_questions raises NoQuizDataError", False)
    except qg.NoQuizDataError:
        check("empty raw_questions raises NoQuizDataError", True)

    try:
        qg.QuizGenerator().load_questions(None)
        check("None raw_questions raises NoQuizDataError", False)
    except qg.NoQuizDataError:
        check("None raw_questions raises NoQuizDataError", True)

    # 5. Mixed valid + malformed entries: malformed is skipped, valid ones still load
    mixed = SAMPLE_RAW + [{"word": "broken", "question": "Missing fields?"}]  # no answer/distractors
    gen2 = qg.QuizGenerator()
    gen2.load_questions(mixed)
    check("malformed entries are skipped while valid ones still load", len(gen2.questions) == 3)

    # 6. All-malformed raw data -> NoQuizDataError
    try:
        qg.QuizGenerator().load_questions([{"word": "x"}])
        check("all-malformed raw data raises NoQuizDataError", False)
    except qg.NoQuizDataError:
        check("all-malformed raw data raises NoQuizDataError", True)

    # 7. get_quiz randomizes selection/order and respects num_questions
    gen3 = qg.QuizGenerator()
    gen3.load_questions(SAMPLE_RAW)
    subset = gen3.get_quiz(num_questions=2)
    check("get_quiz(2) returns exactly 2 questions", len(subset) == 2)
    subset_full = gen3.get_quiz(num_questions=100)
    check("get_quiz caps at the number of available questions", len(subset_full) == 3)

    # 8. Full simulated QuizSession: answer Q1 correctly, Q2 incorrectly
    q1 = qg.QuizQuestion(
        question_text="What does 'a' mean?",
        options={"A": "wrong1", "B": "right1", "C": "wrong2", "D": "wrong3"},
        correct_letter="B",
        word="alpha",
    )
    q2 = qg.QuizQuestion(
        question_text="What does 'b' mean?",
        options={"A": "right2", "B": "wrong4", "C": "wrong5", "D": "wrong6"},
        correct_letter="A",
        word="beta",
    )
    session = qg.QuizSession([q1, q2])

    original_input = builtins.input
    builtins.input = with_inputs(["B", "", "C"])  # correct on q1, [Next], wrong on q2
    try:
        summary = session.run()
    finally:
        builtins.input = original_input

    check("session scores 1/2 correctly", summary["score"] == 1 and summary["total"] == 2)
    check("session records the missed word", summary["missed_words"] == ["beta"])
    check("session computes percent correctly", summary["percent"] == 50.0)

    # 9. save_score() calls into file_manager's record_quiz_score (mocked here)
    saved = {}

    def fake_record(entry):
        saved.update(entry)

    original_record = qg.record_quiz_score
    qg.record_quiz_score = fake_record
    try:
        session.save_score(summary)
    finally:
        qg.record_quiz_score = original_record
    check("save_score() forwards the summary to file_manager.record_quiz_score", saved.get("score") == 1)

    # 10. run_quiz() end-to-end returns None gracefully when quiz data is unavailable
    result = qg.run_quiz([])
    check("run_quiz() with no data returns None instead of crashing", result is None)

    # 11. run_quiz() end-to-end with valid data + simulated input, storage mocked
    saved2 = {}
    qg.record_quiz_score = lambda entry: saved2.update(entry)
    builtins.input = with_inputs(["B", "", "B", "", "A"])  # 3 correct answers for SAMPLE_RAW's 3 Qs
    try:
        result = qg.run_quiz(SAMPLE_RAW, num_questions=3)
    finally:
        builtins.input = original_input
        qg.record_quiz_score = original_record

    # We don't know the shuffled letters ahead of time, so just check the run completed
    # and produced a well-formed, saved summary.
    check("run_quiz() end-to-end returns a summary with score/total/percent",
          result is not None and {"score", "total", "percent", "missed_words"} <= result.keys())
    check("run_quiz() end-to-end persisted the same summary via file_manager", saved2 == result)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: {failures}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
