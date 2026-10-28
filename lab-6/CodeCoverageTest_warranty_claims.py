"""Code (line) coverage tests for warranty_claims.py.

Goal: run every line of warranty_claims.py at least once.
"""
import pytest
from warranty_claims import out_of_warranty_charge, claim_allowed, sla_status


# ---------- out_of_warranty_charge ----------

def test_within_warranty():
    # standard plan covers 24 months, 20 months old -> nothing to pay
    assert out_of_warranty_charge("standard", 20, "defect", False) == 0


def test_unknown_plan_raises_error():
    with pytest.raises(ValueError):
        out_of_warranty_charge("gold", 10, "defect", False)


def test_negative_age_raises_error():
    with pytest.raises(ValueError):
        out_of_warranty_charge("basic", -1, "defect", False)


def test_defect_just_out_of_warranty():
    # basic = 12 months, 20 months old -> 8 extra months at rate 100
    assert out_of_warranty_charge("basic", 20, "defect", False) == 800


def test_registered_accidental_claim():
    # registered basic plan gets 6 extra months -> 18 covered
    # 30 months old -> 12 extra months at rate 200
    assert out_of_warranty_charge("basic", 30, "accidental", True) == 2400


def test_accidental_long_out_of_warranty():
    # basic = 12 months, 40 months old -> 28 extra months
    # rate = 200 + 50 + 25 = 275
    assert out_of_warranty_charge("basic", 40, "accidental", False) == 7700


# ---------- claim_allowed ----------

def test_claim_allowed():
    assert claim_allowed(60, 1, False) is True


def test_claim_too_soon_after_last_claim():
    assert claim_allowed(10, 1, False) is False


def test_recall_claim_allowed():
    assert claim_allowed(5, 4, True) is True


# ---------- sla_status ----------

def test_hardware_on_track():
    # hardware cutoff is 48 hours
    assert sla_status(50, True, False) == "on_track"


def test_hardware_at_risk():
    # 40 hours left is between 36 and 48
    assert sla_status(40, True, False) == "at_risk"


def test_software_priority_critical():
    # software 24 + priority 24 = 48 cutoff, 10 hours is below 36
    assert sla_status(10, False, True) == "critical"
