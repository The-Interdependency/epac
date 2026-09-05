"""Contract tests for personal-console user/root execution separation."""
from __future__ import annotations

# === CHECKS ===
# id: check_vm_mcp_user_exec_non_root
#   proves: vm_mcp_user_exec_non_root
#   call: self::test_user_mode_rejects_root
#   mutates: none
#   cleanup: none
#
# id: check_vm_mcp_admin_exec_explicit_root
#   proves: vm_mcp_admin_exec_explicit_root
#   call: self::test_admin_mode_selects_root
#   mutates: none
#   cleanup: none
#
# id: check_vm_mcp_broker_execution_bounded
#   proves: vm_mcp_broker_execution_bounded
#   call: self::test_admin_execution_timeout_is_bounded_when_root
#   mutates: process
#   cleanup: process_group_killed
#
# id: check_vm_mcp_admin_broker_peer_verified
#   proves: vm_mcp_admin_broker_peer_verified
#   call: self::test_serve_source_uses_peer_credentials
#   mutates: none
#   cleanup: none
# === END CHECKS ===

import pwd
import unittest
from pathlib import Path
from unittest.mock import patch

import admin_broker


class VmMcpAdminBrokerTests(unittest.TestCase):
    def test_user_mode_rejects_root(self) -> None:
        with self.assertRaises(ValueError):
            admin_broker._account_for_request("user", "root")

    def test_admin_mode_selects_root(self) -> None:
        account = admin_broker._account_for_request("admin", None)
        self.assertEqual(account.pw_uid, 0)
        self.assertEqual(account.pw_name, "root")

    def test_user_mode_selects_non_root_account(self) -> None:
        current = pwd.getpwuid(__import__("os").getuid())
        if current.pw_uid == 0:
            self.skipTest("test runner is root; no portable non-root fixture")
        account = admin_broker._account_for_request("user", current.pw_name)
        self.assertEqual(account.pw_uid, current.pw_uid)

    def test_serve_source_uses_peer_credentials(self) -> None:
        text = Path(admin_broker.__file__).read_text(encoding="utf-8")
        self.assertIn("SO_PEERCRED", text)
        self.assertIn("peer_uid != caller.pw_uid", text)
        self.assertIn("os.chmod(socket_path, 0o660)", text)

    def test_admin_execution_timeout_is_bounded_when_root(self) -> None:
        import os
        if os.geteuid() != 0:
            self.skipTest("root broker integration requires root test process")
        result = admin_broker.execute_request({
            "mode": "admin", "command": "sleep 2", "cwd": "/",
            "timeout_seconds": 0.1, "max_output_bytes": 1024,
        })
        self.assertTrue(result["timed_out"])
        self.assertIsNone(result["exit_code"])

    def test_request_rejects_empty_command_before_spawn(self) -> None:
        with patch("admin_broker.os.geteuid", return_value=0), \
             patch("admin_broker.subprocess.Popen") as popen:
            with self.assertRaises(ValueError):
                admin_broker.execute_request({"mode": "admin", "command": "", "cwd": "/"})
        popen.assert_not_called()

    def test_execution_requires_root_broker_process(self) -> None:
        with patch("admin_broker.os.geteuid", return_value=1000), \
             patch("admin_broker.subprocess.Popen") as popen:
            with self.assertRaises(PermissionError):
                admin_broker.execute_request({"mode": "admin", "command": "true", "cwd": "/"})
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
