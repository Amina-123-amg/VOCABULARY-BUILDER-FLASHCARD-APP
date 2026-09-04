# Vocabulary Builder & Smart Flashcard App

## Run

1. Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

2. Create a `.env` file in this folder and add:

```text
GEMINI_API_KEY=your_key_here
```

3. Start Streamlit:

```powershell
py -m streamlit run app.py
```

## Connected modules

- `app.py` — Streamlit UI and application flow
- `dictionary_api.py` — dictionary lookup
- `gemini_client.py` — AI explanations, examples, memory tricks and quizzes
- `models.py` — Word and Flashcard data models
- `spaced_repetition.py` — review scheduling
- `utils/file_manager.py` — JSON persistence
- `exceptions.py` — shared errors
- `services/quiz_generator.py` — quiz-generation/scoring utilities
