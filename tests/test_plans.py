from core.entitlements.service import EntitlementService

def test_three_tier_entitlements():
    s = EntitlementService()
    assert s.competitor_limit("free") == 10
    assert s.competitor_limit("pro") is None
    assert s.competitor_limit("expert") is None
    assert not s.can_use("pro", "consultant")
    assert s.can_use("expert", "consultant")
