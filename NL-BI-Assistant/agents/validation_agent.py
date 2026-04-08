def validate_question(question, df):
    question = question.lower().strip()

    # 🚫 Block only obvious junk
    if question in ["hi", "hello", "hey", ""]:
        return False

    # 🚫 Too short
    if len(question.split()) < 2:
        return False

    return True