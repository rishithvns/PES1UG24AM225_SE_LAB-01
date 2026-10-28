"""Branch coverage tests for warranty_claims.py.

Goal: make every if/else go both ways (True and False),
and check the boundary values where the result changes.
"""
import pytest
from warranty_claims import out_of_warranty_charge, claim_allowed, sla_status


# ---------- out_of_warranty_charge ----------

def test_unknown_plan_raises_error():
    with pytest.raises(ValueError):
        out_of_warranty_charge("gold", 10, "defect", False)


def test_negative_age_raises_error():
    with pytest.raises(ValueError):
        out_of_warranty_charge("basic", -1, "defect", False)


def test_zero_age_is_free():
    # age 0 is valid (not negative)
    assert out_of_warranty_charge("basic", 0, "defect", False) == 0


def test_within_warranty():
    assert out_of_warranty_charge("standard", 20, "defect", False) == 0


def test_exactly_at_end_of_warranty_is_free():
    # excess = 0 -> still free
    assert out_of_warranty_charge("premium", 36, "accidental", False) == 0


def test_registered_extends_basic_plan():
    # registered basic plan covers 12 + 6 = 18 months
    assert out_of_warranty_charge("basic", 18, "defect", True) == 0


def test_registered_does_not_extend_premium():
    # premium does not get the extra 6 months
    # 37 months old -> 1 extra month at rate 100
    assert out_of_warranty_charge("premium", 37, "defect", True) == 100


def test_defect_short_excess():
    # 8 extra months at rate 100
    assert out_of_warranty_charge("basic", 20, "defect", False) == 800


def test_accidental_short_excess():
    # 8 extra months at rate 200
    assert out_of_warranty_charge("basic", 20, "accidental", False) == 1600


def test_excess_exactly_12_has_no_surcharge():
    # 12 extra months is not more than 12, so rate stays 100
    assert out_of_warranty_charge("basic", 24, "defect", False) == 1200


def test_defect_long_excess_surcharge():
    # 13 extra months -> rate 100 + 50 = 150
    assert out_of_warranty_charge("basic", 25, "defect", False) == 1950


def test_accidental_long_excess_surcharge():
    # 13 extra months -> rate 200 + 50 + 25 = 275
    assert out_of_warranty_charge("basic", 25, "accidental", False) == 3575


# ---------- claim_allowed ----------

def test_recall_within_limit():
    assert claim_allowed(5, 5, True) is True


def test_recall_over_limit():
    assert claim_allowed(5, 6, True) is False


def test_recall_ignores_30_day_rule():
    # recall claims are allowed even if the last claim was recent
    assert claim_allowed(0, 1, True) is True


def test_claim_too_soon():
    assert claim_allowed(29, 0, False) is False


def test_claim_exactly_30_days_allowed():
    assert claim_allowed(30, 2, False) is True


def test_too_many_claims():
    assert claim_allowed(60, 3, False) is False


# ---------- sla_status ----------

def test_hardware_on_track_at_cutoff():
    assert sla_status(48, True, False) == "on_track"


def test_hardware_at_risk():
    assert sla_status(40, True, False) == "at_risk"


def test_hardware_at_risk_boundary():
    # cutoff - 12 = 36 is still at risk
    assert sla_status(36, True, False) == "at_risk"


def test_hardware_critical():
    assert sla_status(35, True, False) == "critical"


def test_software_on_track():
    assert sla_status(24, False, False) == "on_track"


def test_software_at_risk():
    assert sla_status(12, False, False) == "at_risk"


def test_software_critical():
    assert sla_status(11, False, False) == "critical"


def test_priority_hardware_cutoff_is_72():
    assert sla_status(72, True, True) == "on_track"
    assert sla_status(71, True, True) == "at_risk"


def test_priority_software_critical():
    # software 24 + priority 24 = 48 cutoff
    assert sla_status(10, False, True) == "critical"
