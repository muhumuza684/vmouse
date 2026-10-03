import platform_utils as pu
import system_handler as sh


def test_every_power_action_has_a_command_or_is_declared_unsupported():
    for action in pu.POWER_ACTIONS:
        entry = pu.power_command(action)
        assert entry is None or (isinstance(entry[0], str) and isinstance(entry[1], str))


def test_unknown_power_action_is_rejected():
    assert sh.execute_system_power("explode")["status"] == "error"


def test_windows_key_names(monkeypatch):
    monkeypatch.setattr(pu, "IS_WIN", True)
    monkeypatch.setattr(pu, "IS_MAC", False)
    assert pu.adapt_keys(["super", "d"]) == ["win", "d"]
    assert pu.adapt_keys(["ctrl", "c"]) == ["ctrl", "c"]


def test_mac_uses_command_for_shortcuts(monkeypatch):
    monkeypatch.setattr(pu, "IS_WIN", False)
    monkeypatch.setattr(pu, "IS_MAC", True)
    assert pu.adapt_keys(["ctrl", "c"]) == ["command", "c"]
    assert pu.adapt_keys(["win", "d"]) == ["command", "d"]


def test_blocked_and_unknown_commands_do_not_run():
    for cmd in ("powershell", "rm -rf /", "del x", "sudo ls", "curl http://x", "python -c 1", "notacommand"):
        assert sh.execute_custom_command(cmd)["status"] == "blocked", cmd


def test_chaining_is_refused():
    for cmd in ("echo hi & whoami", "echo hi | more", "echo hi; whoami", "echo hi > file", "echo `id`", "echo $(id)"):
        assert sh.execute_custom_command(cmd)["status"] == "blocked", cmd


def test_empty_command():
    assert sh.execute_custom_command("   ")["status"] == "error"


def test_allowed_command_runs():
    out = sh.execute_custom_command("echo vmouse")
    assert out["status"] == "success" and "vmouse" in out["output"]


def test_open_app_rejects_odd_names(monkeypatch):
    monkeypatch.setattr(pu, "IS_WIN", False)
    monkeypatch.setattr(pu, "IS_MAC", False)
    ok, _ = pu.open_app("calc; rm -rf /")
    assert ok is False
