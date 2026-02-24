def calculate_risk(score, attempts, time_taken):

    risk = 0

    # Low score increases risk
    if score < 50:
        risk += 40

    # Multiple attempts increases risk
    if attempts > 2:
        risk += 30

    # Taking too long increases risk
    if time_taken > 300:
        risk += 30

    return min(risk, 100)