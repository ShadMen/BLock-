from backend.security.async_ratchet import RatchetState


def test_ratchet_encrypt_decrypt():
    rk = b"r" * 32
    ck_ab = b"a" * 32
    ck_ba = b"b" * 32

    alice = RatchetState(root_key=rk, send_chain_key=ck_ab, recv_chain_key=ck_ba)
    bob = RatchetState(root_key=rk, send_chain_key=ck_ba, recv_chain_key=ck_ab)

    idx, nonce, ct = alice.encrypt_message(b"hello")
    pt = bob.decrypt_message(idx, nonce, ct)
    assert pt == b"hello"


def test_ratchet_supports_out_of_order_delivery():
    rk = b"r" * 32
    ck_ab = b"a" * 32
    ck_ba = b"b" * 32

    alice = RatchetState(root_key=rk, send_chain_key=ck_ab, recv_chain_key=ck_ba)
    bob = RatchetState(root_key=rk, send_chain_key=ck_ba, recv_chain_key=ck_ab)

    m0 = alice.encrypt_message(b"zero")
    m1 = alice.encrypt_message(b"one")

    pt1 = bob.decrypt_message(*m1)
    pt0 = bob.decrypt_message(*m0)

    assert pt1 == b"one"
    assert pt0 == b"zero"


def test_ratchet_rejects_excessive_skip_window():
    rk = b"r" * 32
    ck_ab = b"a" * 32
    ck_ba = b"b" * 32

    alice = RatchetState(root_key=rk, send_chain_key=ck_ab, recv_chain_key=ck_ba)
    bob = RatchetState(root_key=rk, send_chain_key=ck_ba, recv_chain_key=ck_ab)

    for _ in range(1002):
        far_message = alice.encrypt_message(b"x")

    try:
        bob.decrypt_message(*far_message)
        assert False, "expected ValueError for too-far future index"
    except ValueError as exc:
        assert str(exc) == "message index too far in future"
