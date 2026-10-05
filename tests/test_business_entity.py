from core.business.entity import BusinessEntity
from core.business.repository import InMemoryBusinessRepository


def test_business_entity_round_trips_through_repository():
    repo = InMemoryBusinessRepository()
    business = BusinessEntity(
        id="biz-1",
        name="Example Coffee",
        country_code="KR",
        business_type="cafe",
        channel="local",
        goal="improve margin",
    )
    saved = repo.save(business)
    loaded = repo.get("biz-1")
    assert loaded == saved
    assert loaded is not saved


def test_business_repository_does_not_expose_mutable_internal_state():
    repo = InMemoryBusinessRepository()
    repo.save(BusinessEntity(
        id="biz-1", name="Example", country_code="KR",
        business_type="service", channel="local",
    ))
    loaded = repo.get("biz-1")
    assert loaded is not None
    loaded.profile["x"] = "changed"
    assert repo.get("biz-1").profile == {}
