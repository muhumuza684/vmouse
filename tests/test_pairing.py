import json
import ssl

import pairing


def test_token_is_created_and_kept(tmp_path):
    first = pairing.PairingStore(tmp_path)
    again = pairing.PairingStore(tmp_path)
    assert len(first.token) >= 16
    assert first.token == again.token


def test_reset_makes_a_new_token(tmp_path):
    store = pairing.PairingStore(tmp_path)
    old = store.token
    assert store.reset() != old
    assert pairing.PairingStore(tmp_path).token == store.token


def test_broken_file_is_replaced(tmp_path):
    (tmp_path / "pairing.json").write_text("not json")
    assert len(pairing.PairingStore(tmp_path).token) >= 16


def test_web_switch_is_saved(tmp_path):
    store = pairing.PairingStore(tmp_path)
    assert store.allow_web is True
    store.set_allow_web(False)
    assert pairing.PairingStore(tmp_path).allow_web is False


def test_guard_accepts_right_and_rejects_wrong(tmp_path):
    guard = pairing.PairingGuard(pairing.PairingStore(tmp_path))
    assert guard.check("1.2.3.4", guard.store.token) == (True, "ok")
    assert guard.check("1.2.3.4", "wrong") == (False, "bad_token")
    assert guard.check("1.2.3.4", None) == (False, "bad_token")
    assert guard.check("1.2.3.4", "") == (False, "bad_token")


def test_guard_blocks_after_repeated_failures_then_recovers(tmp_path):
    clock = {"t": 1000.0}
    guard = pairing.PairingGuard(pairing.PairingStore(tmp_path), now=lambda: clock["t"])
    for _ in range(pairing.MAX_FAILURES):
        guard.check("9.9.9.9", "bad")
    assert guard.check("9.9.9.9", guard.store.token) == (False, "blocked")
    assert guard.check("8.8.8.8", guard.store.token) == (True, "ok")  # other phones are not affected
    clock["t"] += pairing.BLOCK_SECONDS + 1
    assert guard.check("9.9.9.9", guard.store.token) == (True, "ok")


def test_pairing_url_has_everything_the_phone_needs():
    url = pairing.pairing_url("192.168.1.20", "tok", "abcd", tls=True)
    assert url.startswith("http://192.168.1.20:8080/?")
    for part in ("k=tok", "fp=abcd", "tls=1", "wss=8765", "ws=8766"):
        assert part in url


def test_private_address_check():
    assert pairing._is_private("192.168.0.5") and pairing._is_private("10.1.2.3") and pairing._is_private("172.20.1.1")
    assert not pairing._is_private("8.8.8.8") and not pairing._is_private("172.32.0.1")


def test_firewall_command_names_every_port():
    cmd = pairing.firewall_commands()
    for port in (pairing.WS_SECURE_PORT, pairing.WS_PLAIN_PORT, pairing.HTTP_PORT, pairing.HTTPS_PORT):
        assert str(port) in cmd


def test_certificate_fingerprint_matches(tmp_path):
    from OpenSSL import crypto
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    cert = crypto.X509()
    cert.get_subject().CN = "vmouse-test"
    cert.set_serial_number(1)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(3600)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha256")
    pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode()
    path = tmp_path / "cert.pem"
    path.write_text(pem)
    import hashlib
    assert pairing.cert_fingerprint(path) == hashlib.sha1(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()
