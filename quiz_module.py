import random

# Cache for generated questions
questions_cache = []

# Question type templates
QUESTION_TEMPLATES = {
    "main_idea": "What is the main idea of: '{sentence}'?",
    "inference": "What can be inferred from: '{sentence}'?",
    "fill_blank": "Fill in the blank: '{}'",
    "true_false": "Is the following statement true or false? '{}'"
}

def generate_quiz(summary):
    """Generates a quiz with 5 diverse types of questions."""
    global questions_cache

    if not summary.strip():
        return {"error": "No summary available. Generate a summary first."}

    sentences = [s.strip() for s in summary.split('.') if len(s.strip()) > 20]
    if not sentences:
        return {"error": "Generate Summary to get your Quiz."}

    question_types = list(QUESTION_TEMPLATES.keys())
    random.shuffle(question_types)  # Ensure unique types in random order

    # Make sure we have enough sentences
    used_sentences = sentences[:5] if len(sentences) >= 5 else (sentences * (5 // len(sentences) + 1))[:5]

    questions = []

    for i in range(5):
        q_type = question_types[i % len(question_types)]
        sentence = used_sentences[i % len(used_sentences)]
        question = ""
        choices = []
        answer = sentence  # default

        if q_type == "fill_blank":
            words = sentence.split()
            if len(words) < 4:
                continue
            blank_index = random.randint(1, len(words) - 2)
            answer = words[blank_index]
            words[blank_index] = "_____"
            blank_sentence = ' '.join(words)
            question = QUESTION_TEMPLATES[q_type].format(blank_sentence)
            choices = [answer, "random1", "random2", "random3"]
            random.shuffle(choices)

        elif q_type == "true_false":
            is_true = random.choice([True, False])
            altered_sentence = sentence if is_true or len(sentences) == 1 else random.choice([s for s in sentences if s != sentence])
            answer = "True" if altered_sentence == sentence else "False"
            question = QUESTION_TEMPLATES[q_type].format(altered_sentence)
            choices = ["True", "False"]

        elif q_type == "main_idea":
            question = QUESTION_TEMPLATES[q_type].format(sentence=sentence)
            distractors = [s for s in sentences if s != sentence]
            incorrects = random.sample(distractors, min(2, len(distractors))) + ["Unrelated option"]
            choices = incorrects + [answer]
            random.shuffle(choices)

        elif q_type == "inference":
            question = QUESTION_TEMPLATES[q_type].format(sentence=sentence)
            distractors = [s for s in sentences if s != sentence]
            incorrects = random.sample(distractors, min(2, len(distractors))) + ["Unrelated conclusion"]
            choices = incorrects + [answer]
            random.shuffle(choices)

        questions.append({
            "question": question,
            "choices": choices,
            "answer": answer
        })

    if not questions:
        return {"error": "Could not generate any valid quiz questions. Try providing more detailed summary content."}

    questions_cache = questions
    return {"quiz": questions}

# Submit function remains unchanged
def submit_quiz(user_answers):
    """Evaluate user answers and return their score."""
    global questions_cache
    if not questions_cache:
        return {"error": "No quiz available to evaluate. Generate a quiz first."}

    score = 0
    for idx, question in enumerate(questions_cache):
        if user_answers.get(str(idx)) == question["answer"]:
            score += 1

    return {"score": score, "total": len(questions_cache)}
