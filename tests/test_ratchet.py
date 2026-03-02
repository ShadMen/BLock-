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
