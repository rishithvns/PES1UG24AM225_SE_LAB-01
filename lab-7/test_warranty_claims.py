import math

from hypothesis import given, strategies as st
from warranty_claims import parse_claim, age_average, payable_charge


# ---------- Fuzz tests: the functions must never crash, whatever the input ----------

@given(st.text() | st.none())
def test_parse_claim_no_crash(s):
    try:
        parse_claim(s)
    except Exception as e:
        assert False, f"parse_claim crashed with: {e!r} for input {s!r}"


@given(st.text() | st.none())
def test_age_average_no_crash(s):
    try:
        age_average(s)
    except Exception as e:
        assert False, f"age_average crashed with: {e!r} for input {s!r}"


@given(st.text() | st.none())
def test_payable_charge_no_crash(s):
    try:
        payable_charge(s)
    except Exception as e:
        assert False, f"payable_charge crashed with: {e!r} for input {s!r}"


# ---------- Targeted fuzzing: inputs that look almost valid ----------
# Plain st.text() rarely produces a ':' , ',' or '|' in the right place, so these
# strategies build strings out of the characters the functions actually care about.

claim_like = st.text(alphabet="abc :0123456789.-+einfa", max_size=15)
csv_like = st.text(alphabet="0123456789,- .a", max_size=15)
charge_like = st.text(alphabet="0123456789|.-+einfa ", max_size=15)


@given(claim_like)
def test_parse_claim_result_is_sane(s):
    result = parse_claim(s)
    if result is not None:
        plan, months = result
        assert plan != ""
        assert math.isfinite(months) and months >= 0   # no nan / inf / negative age


@given(csv_like)
def test_age_average_result_is_sane(s):
    result = age_average(s)
    if result is not None:
        assert isinstance(result, int) and result >= 0


@given(charge_like)
def test_payable_charge_result_is_sane(s):
    result = payable_charge(s)
    if result is not None:
        assert math.isfinite(result) and result >= 0   # never nan / inf / negative


# ---------- Valid inputs must still give the correct answer ----------

@given(st.lists(st.integers(min_value=0, max_value=600), min_size=1))
def test_age_average_valid_input(ages):
    csv = ",".join(str(a) for a in ages)
    assert age_average(csv) == sum(ages) // len(ages)


@given(st.integers(min_value=0, max_value=100000), st.integers(min_value=0, max_value=100000))
def test_payable_charge_valid_input(charge, discount):
    assert payable_charge(f"{charge}|{discount}") == max(charge * 1.18 - discount, 0)


@given(st.sampled_from(["standard", "premium", "basic"]), st.integers(min_value=0, max_value=600))
def test_parse_claim_valid_input(plan, months):
    assert parse_claim(f"{plan}:{months}") == (plan.title(), float(months))
