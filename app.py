import streamlit as st

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------

st.set_page_config(
    page_title="Vocabulary Builder",
    page_icon="📚",
    layout="wide"
)


# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("📚 Vocabulary Builder")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🔍 Search Word",
        "🃏 Flashcards",
        "🧠 Review",
        "❓ Quiz",
        "📊 Progress"
    ]
)


# -----------------------------
# HOME PAGE
# -----------------------------

if page == "🏠 Home":

    st.title("📚 Vocabulary Builder")

    st.subheader("Expand your vocabulary, one word at a time.")

    st.write(
        "Search for new words, create flashcards, "
        "take quizzes and track your progress."
    )

    st.divider()

    st.subheader("📊 Your Learning Progress")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Words Learned", 0)

    with col2:
        st.metric("Flashcards", 0)

    with col3:
        st.metric("Quiz Accuracy", "0%")


# -----------------------------
# SEARCH PAGE
# -----------------------------

elif page == "🔍 Search Word":

    st.title("🔍 Search for a Word")

    word = st.text_input(
        "Enter a word",
        placeholder="e.g. magnificent"
    )

    if st.button("Search"):

        if word.strip() == "":
            st.warning("Please enter a word.")

        else:
            st.success(f"Searching for: {word}")


# -----------------------------
# FLASHCARDS PAGE
# -----------------------------

elif page == "🃏 Flashcards":

    st.title("🃏 My Flashcards")

    st.write("Your saved vocabulary flashcards will appear here.")

    st.info("You don't have any flashcards yet.")


# -----------------------------
# REVIEW PAGE
# -----------------------------

elif page == "🧠 Review":

    st.title("🧠 Review")

    st.write("Review the words that are due for revision.")

    st.info("No flashcards are currently due for review.")


# -----------------------------
# QUIZ PAGE
# -----------------------------

elif page == "❓ Quiz":

    st.title("❓ Vocabulary Quiz")

    st.write("Test your vocabulary knowledge.")

    st.info("Your quiz will appear here.")


# -----------------------------
# PROGRESS PAGE
# -----------------------------

elif page == "📊 Progress":

    st.title("📊 Learning Progress")

    st.write("Track your vocabulary learning progress here.")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Words", 0)

    with col2:
        st.metric("Quizzes Taken", 0)