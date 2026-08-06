print("Hello, I am your Cognitive AI assistant.")
print("I will analyze situations using the 5W1H thinking method.\n")

questions = [
    "Who is involved in the situation? ",
    "What is happening? ",
    "When did it occur? ",
    "Where did it occur? ",
    "Why do you think it happened? ",
    "How could it be solved? "
]

answers = []

for q in questions:
    answer = input(q)
    answers.append(answer)

print("\n--- Cognitive Summary ---")

labels = ["Who", "What", "When", "Where", "Why", "How"]

for i in range(len(labels)):
    print(labels[i] + ":", answers[i])

print("\nThank you. Analysis complete.")

if "conflict" in answers[1].lower():
    print("\nAI Follow-Up: What caused the conflict?")

print("Hello. I am CognitionAI.")
print("My purpose is to investigate situations using analytical reasoning.")
print("Let's begin our investigation.\n")