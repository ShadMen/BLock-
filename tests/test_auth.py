from backend.services.auth import generate_totp, is_google_email, verify_totp


def test_google_domain_check():
    assert is_google_email("user@gmail.com")
    assert is_google_email("user@googlemail.com")
    assert not is_google_email("user@yahoo.com")


def test_totp_roundtrip():
    secret = "JBSWY3DPEHPK3PXP"  # base32
    ts = 1700000000
    code = generate_totp(secret, ts)
    assert verify_totp(secret, code, ts)
