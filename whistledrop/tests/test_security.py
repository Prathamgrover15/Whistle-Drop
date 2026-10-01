from app.security import (
    generate_case_code,
    hash_case_code,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_case_code_has_expected_prefix_and_length():
    code = generate_case_code()
    assert code.startswith("WD-")
    assert len(code) > 20  # WD- + 18 random bytes, base64-encoded


def test_case_codes_are_unique():
    codes = {generate_case_code() for _ in range(50)}
    assert len(codes) == 50


def test_hash_is_deterministic():
    code = "WD-abc123"
    assert hash_case_code(code) == hash_case_code(code)


def test_different_codes_hash_differently():
    assert hash_case_code("WD-aaaa") != hash_case_code("WD-bbbb")


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_roundtrip():
    token = create_access_token(subject="some-moderator-id")
    assert decode_access_token(token) == "some-moderator-id"


def test_jwt_rejects_garbage():
    assert decode_access_token("not-a-real-token") is None
