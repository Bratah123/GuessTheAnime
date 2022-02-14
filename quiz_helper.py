import json

with open("trivia_questions.json", "r") as f:
    trivia_questions = json.load(f)

while True:
    question = input("Enter the question: ")
    answer = input("Enter the answer: ")
    answers = input("Enter the other answer options: ")
    answers = answers.split(", ")
    answers.append(answer)
    entry = {
        "question": question,
        "answers": answers,
        "answer": answer
    }
    trivia_questions.append(entry)
    print("Successfully inputted into trivia database")
    yn = input("end program? ")
    if yn == 'y':
        break
    if yn == 'revert':
        trivia_questions.pop()
        print("Removed the last entry...")

with open("trivia_questions.json", "w") as f:
    json.dump(trivia_questions, f, indent=4)

print("Successfully saved everything into trivia database")
