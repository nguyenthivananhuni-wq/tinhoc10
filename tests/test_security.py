from app.security import (
    hash_password,
    sign_session,
    unsign_session,
    verify_password,
)


def test_hash_then_verify_correct():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h) is True


def test_verify_wrong_password():
    h = hash_password("secret123")
    assert verify_password("wrong", h) is False


def test_hash_is_random_salt():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salt makes hashes differ


def test_session_roundtrip():
    token = sign_session(42)
    assert isinstance(token, str)
    uid = unsign_session(token)
    assert uid == 42


def test_unsign_invalid_returns_none():
    assert unsign_session("garbage") is None
    assert unsign_session("") is None


def test_unsign_tampered_returns_none():
    token = sign_session(7)
    # Flip one character in the signature portion
    tampered = token[:-2] + ("A" if token[-1] != "A" else "B") + token[-1]
    assert unsign_session(tampered) is None
