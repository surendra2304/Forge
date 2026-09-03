from forge_upgrade.persistence.idempotency import IdempotencyStore


def test_idempotency():
    s = IdempotencyStore()
    k = s.make_key("t", "i")
    assert not s.seen(k)
    s.remember(k, "r")
    assert s.seen(k)
