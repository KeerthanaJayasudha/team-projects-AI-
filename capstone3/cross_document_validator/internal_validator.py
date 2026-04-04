from rapidfuzz.fuzz import token_sort_ratio


def check_consistency(values, threshold=85):

    if len(values) <= 1:
        return True

    base = values[0]

    for value in values[1:]:

        score = token_sort_ratio(base.lower(), value.lower())

        if score < threshold:
            return False

    return True