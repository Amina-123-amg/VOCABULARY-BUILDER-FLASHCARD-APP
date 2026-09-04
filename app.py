import streamlit as st

from dictionary_api import DictionaryClient
from exceptions import VocabAppError
from gemini_client import GeminiClient, GeminiError
from models import Word, Flashcard
from spaced_repetition import SpacedRepetitionService
from utils.file_manager import (
    load_saved_words, save_word, remove_word,
    load_flashcards, save_flashcard, remove_flashcard,
    load_quiz_scores, record_quiz_score,
)

st.set_page_config(page_title="Vocabulary Builder", page_icon="📚", layout="wide")

# ---------- session state ----------
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "ai_data" not in st.session_state:
    st.session_state.ai_data = {}
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_saved" not in st.session_state:
    st.session_state.quiz_saved = False


def get_ai():
    try:
        return GeminiClient()
    except GeminiError:
        return None


def word_to_record(word: Word):
    data = word.to_dict()
    data.update(st.session_state.ai_data.get(word.text, {}))
    return data


def load_saved_word_objects():
    return {k: Word.from_dict(v) for k, v in load_saved_words().items()}

# ---------- sidebar ----------
st.sidebar.title("📚 Vocabulary Builder")
page = st.sidebar.radio("Navigation", [
    "🏠 Home", "🔍 Search Word", "🃏 Flashcards", "🧠 Review", "❓ Quiz", "📊 Progress"
])

saved_words = load_saved_words()
flashcards = load_flashcards()
quiz_scores = load_quiz_scores()

# ---------- HOME ----------
if page == "🏠 Home":
    st.title("📚 Vocabulary Builder")
    st.subheader("Expand your vocabulary, one word at a time.")
    st.write("Search words, use AI learning aids, save flashcards, review them and test yourself.")
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Words Saved", len(saved_words))
    with c2: st.metric("Flashcards", len(flashcards))
    with c3:
        accuracy = (sum(x.get("percent", 0) for x in quiz_scores) / len(quiz_scores)) if quiz_scores else 0
        st.metric("Quiz Accuracy", f"{accuracy:.0f}%")

# ---------- SEARCH ----------
elif page == "🔍 Search Word":
    st.title("🔍 Search for a Word")
    query = st.text_input("Enter a word", placeholder="e.g. magnificent")
    if st.button("Search", type="primary"):
        try:
            client = DictionaryClient()
            result = client.get_word(query)
            st.session_state.current_word = result
            st.session_state.ai_data = {}
            st.success(f"Found: {result.text}")
        except VocabAppError as exc:
            st.error(str(exc))

    word = st.session_state.current_word
    if word:
        st.divider()
        st.header(word.text)
        if word.phonetic: st.write(f"**Phonetics:** {word.phonetic}")
        st.write(f"**Part of speech:** {word.part_of_speech}")
        st.write(f"**Definition:** {word.primary_definition}")
        if word.primary_example: st.write(f"**Example:** {word.primary_example}")
        st.write(f"**Synonyms:** {', '.join(word.all_synonyms) or 'None available'}")
        st.write(f"**Antonyms:** {', '.join(word.all_antonyms) or 'None available'}")

        ai = get_ai()
        if ai:
            if st.button("✨ Generate AI Learning Aids"):
                with st.spinner("Gemini is generating learning aids..."):
                    try:
                        st.session_state.ai_data = {
                            word.text: {
                                "simple_explanation": ai.generate_explanation(word.text),
                                "ai_examples": [ai.generate_example(word.text)],
                                "memory_trick": ai.generate_memory_trick(word.text),
                            }
                        }
                    except GeminiError as exc:
                        st.error(str(exc))
            extra = st.session_state.ai_data.get(word.text, {})
            if extra:
                st.info(f"**Simple explanation:** {extra.get('simple_explanation', '')}")
                st.write(f"**AI example:** {extra.get('ai_examples', [''])[0]}")
                st.write(f"**Memory trick:** {extra.get('memory_trick', '')}")
        else:
            st.caption("Gemini is not configured. Add GEMINI_API_KEY to .env to enable AI features.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Word"):
                save_word(word.text, word_to_record(word))
                st.success("Word saved!")
        with col2:
            if st.button("🃏 Create Flashcard"):
                extra = st.session_state.ai_data.get(word.text, {})
                card = Flashcard(
                    word=word.text,
                    front=word.text,
                    back=extra.get("simple_explanation") or word.primary_definition,
                )
                save_flashcard(word.text, card.to_dict())
                st.success("Flashcard created!")

# ---------- FLASHCARDS ----------
elif page == "🃏 Flashcards":
    st.title("🃏 My Flashcards")
    cards = load_flashcards()
    if not cards:
        st.info("No flashcards yet. Search a word and create one.")
    for key, data in cards.items():
        with st.expander(f"📖 {key}"):
            st.write(f"**Meaning:** {data.get('back', '')}")
            st.write(f"**Next review:** {data.get('due_date', 'Today')}")
            if st.button("Delete", key=f"delete_{key}"):
                remove_flashcard(key)
                st.rerun()

# ---------- REVIEW ----------
elif page == "🧠 Review":
    st.title("🧠 Review")
    cards = load_flashcards()
    due = SpacedRepetitionService.get_due_cards(list(cards.values()))
    if not due:
        st.success("🎉 No flashcards are due today!")
    else:
        st.write(f"**{len(due)} card(s) due for review.**")
        for i, card in enumerate(due):
            st.subheader(card.get("word", "Word"))
            st.write(f"**Meaning:** {card.get('back', '')}")
            cols = st.columns(4)
            for col, rating in zip(cols, ["again", "hard", "good", "easy"]):
                with col:
                    if st.button(rating.title(), key=f"review_{i}_{rating}"):
                        updated = SpacedRepetitionService.update_review(card, rating)
                        save_flashcard(card["word"], updated)
                        st.rerun()
            st.divider()

# ---------- QUIZ ----------
elif page == "❓ Quiz":
    st.title("❓ Vocabulary Quiz")
    ai = get_ai()
    saved = load_saved_words()
    if not ai:
        st.warning("Gemini is not configured. Add GEMINI_API_KEY to .env to use quizzes.")
    elif not saved:
        st.info("Save some words first, then come back for a quiz.")
    else:
        selected = st.multiselect("Choose words", list(saved.keys()), default=list(saved.keys())[:3])
        if st.button("Generate Quiz", type="primary") and selected:
            questions = []
            with st.spinner("Generating quiz..."):
                try:
                    for word_text in selected:
                        q = ai.generate_quiz(word_text)
                        q["word"] = word_text
                        questions.append(q)
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_saved = False
                except GeminiError as exc:
                    st.error(str(exc))

        questions = st.session_state.quiz_questions
        if questions:
            st.divider()
            for i, q in enumerate(questions):
                st.write(f"**{i+1}. {q['question']}**")
                st.session_state.quiz_answers[i] = st.radio(
                    "Choose an answer:", q["options"], key=f"quiz_{i}", index=None
                )
            if st.button("Submit Quiz", type="primary"):
                score = sum(st.session_state.quiz_answers.get(i) == q["correct_answer"] for i, q in enumerate(questions))
                total = len(questions)
                percent = round(score / total * 100, 1)
                record_quiz_score({"score": score, "total": total, "percent": percent})
                st.session_state.quiz_saved = True
                st.success(f"🎉 Score: {score}/{total} ({percent}%)")
                for i, q in enumerate(questions):
                    if st.session_state.quiz_answers.get(i) != q["correct_answer"]:
                        st.write(f"❌ {q['word']}: Correct answer — **{q['correct_answer']}**")

# ---------- PROGRESS ----------
elif page == "📊 Progress":
    st.title("📊 Learning Progress")
    saved = load_saved_words(); cards = load_flashcards(); scores = load_quiz_scores()
    c1, c2, c3 = st.columns(3)
    c1.metric("Words Saved", len(saved)); c2.metric("Flashcards", len(cards)); c3.metric("Quizzes Taken", len(scores))
    if scores:
        st.subheader("Quiz History")
        st.dataframe(scores, use_container_width=True)
