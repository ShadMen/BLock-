from backend.services.contact_discovery import discover_contacts, phone_token


def test_discover_contacts():
    pepper = b"server-pepper"
    registered = {phone_token("+15550001111", pepper)}
    book = ["+1 (555) 000-1111", "+1 555 000 2222"]

    out = discover_contacts(book, pepper, registered)
    assert out == ["+15550001111"]
