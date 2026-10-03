from core.entitlements.service import EntitlementService
def test_free_limit():
 s=EntitlementService(); assert s.can_add_competitor("free",9); assert not s.can_add_competitor("free",10)
def test_pro_unlimited(): assert EntitlementService().can_add_competitor("pro",10000)
