# VOCABULARY-BUILDER-FLASHCARD-APP
Python Advanced Group Project -- Vocabulary Builder and Smart Flashcard App
import random
import os
import json
import genai


def get_questions_from_gemini(topic,number_of_questions):
    prompt = f""
    create {number_of_questions} multiple-choice quiz get_questions_from_gemini
    about {topic}.

    return ONLY valid JSON in this exact format:

    [
        {{
            "question":"question here",
            "option":[
                "option 1",
                "option 2",
                "option 3",
                "option 4"
            ],
            "answer":"option 1"
        }}
    ]
Rules:
-Each question must have exactly four options.
-Only one option must be correct.
-The answer field must contain the exact correct option.
-Do not include explanations
""

try:
    resonse=client.models.generate_content(model = "gemini-2.5-flash",)
    #Remove possible markdown code fences text = response.text.strip()
    if text starts with ("'''")
       text = text.replace("'''json","")
       text = text.replace("''',"")""" 
       text = text.strip()

       questions = json.loads(text)

       return get_questions_from_gemini

       except.json.JSONDecodeError:
    pint("Error commuinicating with Gemini AI:",error)
    return
    

    #-------------------------------------------
    # DISPLAY ONE QUESTION
    #-------------------------------------------

    def display_question(question_data,question_number):
    
    print("\n" + = * 60)
    print(f"Question{question_number}")
    print("=" * 60)

    print(question_data["question"])

    # Make a copy so the original data is not changed
    options = question_data["options"].copy()

 # Randonly shuffle the options
    random.shuffle(options)

    #Display options
    for index, option in enumerate(options):
    letter = chr(65 + index) # A, B, C, D
    print(f"{letter}. {option}")

    # Get user's answer
    while True:
    try:
    answer = input("\nselect your answer (A-D):").strip().upper()
    if answer not in ["A", "B", "C" OR "D"]
    selected_option = options[ord(answer) -65]
     
     return selected_option

     except ValueError as KeyError
     print("invalid input",error)

def run_quiz(question):

score = 0
total_questions =len(questions)

# Randomize the order of the questions
random.shuffle(questions)

for number, question in enumerate(questions,start=1):

selected_answer == correct answer:
print("\ncorrect!")
score += 1
else:
print("\nWrong!")
print("correct answer:",correct_answer)
return score,total_questions

def save_score(score, total, topic):
percentage = (score/total)* 100
try:
 filename = "quiz_results.txt"

 with open(filename, "w") as file:
 file.write(=======\n")
            file.write("QUIZ FINAL RESULT\n")
            file.write(f"score:{score}/{total}\n")
            file.write(f"percentage:{percentage:{percentage:.2f}%\n\n")
                       
            if percentage>=70:
            file.write("result:PASSED\n")
            else:
            file.write("Result:FAILED\n")

            print("\nFinal result saved successfully!")
            print("file:",os.path.absoath(filename)
                  
                  except PermissionError:
                  print("Error:Permission denied.the file could not be saved.")

                  excepy OSError as error:
                  print("Error saving the result:", error)


def main():

print("="*60)
print("  AI LOGICAL QUIZ SYSTEM")
print("="*60)

topic=input("\nEnter the quiz question")
if not questions:
print("no questions available:)"
" Randomly select/shuffle questions"
"random. shuffle(questions)"

score = 0

print("\n""="*50)
print("="850)

for number,questionin enumerate(questions,start=1):
options=

display_question(question,number)
user_answer=get_answer(
    selected_opyion==question["answer"
    "print("correct!")
    score+ =1
    else print("wrong!")
calculate final score
total = len(get_questions_from_gemini)
percentage = (score/total)*100
print("\n" + "=" *50)
print("    QUIZ FINISHED")
print ("=" *50)
print("final score: {score/total}"
)
#save file using file handler.
