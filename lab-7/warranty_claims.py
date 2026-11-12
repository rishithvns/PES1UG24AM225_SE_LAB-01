import math


def _to_number(value):
    """Convert text to a finite, non-negative float. Returns None if it can't."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or number < 0:
        return None          # rejects nan, inf, -inf and negative values
    return number


def parse_claim(text):
    """Parse 'plan:months' -> (Plan, months). Returns None for invalid input."""
    if not isinstance(text, str):
        return None
    parts = text.split(':')
    if len(parts) != 2:      # no colon, or more than one colon
        return None
    plan = parts[0].strip()
    months = _to_number(parts[1])
    if not plan or months is None:
        return None
    return plan.title(), months


def age_average(ages_csv):
    """Floor average of comma separated ages. Returns None for invalid input."""
    if not isinstance(ages_csv, str):
        return None
    values = []
    for item in ages_csv.split(','):
        try:
            age = int(item)
        except (TypeError, ValueError):
            return None      # empty element, letters, decimals, symbols...
        if age < 0:
            return None      # an age can't be negative
        values.append(age)
    if not values:
        return None
    return sum(values) // len(values)


def payable_charge(text):
    """Parse 'charge|discount' -> charge + 18% tax - discount (never below 0).
    Returns None for invalid input."""
    if not isinstance(text, str):
        return None
    parts = text.split('|')
    if len(parts) != 2:      # no pipe, or more than one pipe
        return None
    charge = _to_number(parts[0])
    discount = _to_number(parts[1])
    if charge is None or discount is None:
        return None
    total = charge * 1.18 - discount
    if not math.isfinite(total):
        return None          # charge so large that the result overflows
    return max(total, 0)


def main():
    print("==== Running parse_claim ====")
    user_input = input("Enter plan:age in months (e.g. standard:30): ")
    result = parse_claim(user_input)
    if result is None:
        print("Invalid input. Expected format plan:months, e.g. standard:30")
    else:
        print("Plan and Age:", result)

    print("\n==== Running age_average ====")
    user_input = input("Enter product ages as CSV (e.g. 12,24,36): ")
    result = age_average(user_input)
    if result is None:
        print("Invalid input. Expected whole numbers separated by commas, e.g. 12,24,36")
    else:
        print("Average Age:", result)

    print("\n==== Running payable_charge ====")
    user_input = input("Enter charge|discount (e.g. 1500|200): ")
    result = payable_charge(user_input)
    if result is None:
        print("Invalid input. Expected format charge|discount, e.g. 1500|200")
    else:
        print("Payable Charge:", result)


if __name__ == "__main__":
    main()
