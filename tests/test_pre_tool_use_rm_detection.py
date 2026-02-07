import importlib.util
from pathlib import Path
import unittest


HOOK_PATH = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "pre_tool_use.py"

spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
pre_tool_use = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(pre_tool_use)


class TestDangerousRmDetection(unittest.TestCase):
    def test_path_substring_not_treated_as_flag(self):
        cmd = (
            "rm /Users/me/project/soft-hold-enrollment/db/migrate/20251212031504_add_payment.rb "
            "/Users/me/project/soft-hold-enrollment/db/migrate/foobar.rb"
        )
        self.assertFalse(pre_tool_use.is_dangerous_rm_command(cmd))

    def test_rm_rf_root_is_blocked(self):
        self.assertTrue(pre_tool_use.is_dangerous_rm_command("rm -rf /"))

    def test_rm_r_dot_is_blocked(self):
        self.assertTrue(pre_tool_use.is_dangerous_rm_command("rm -r ."))

    def test_sudo_rm_rf_is_blocked(self):
        self.assertTrue(pre_tool_use.is_dangerous_rm_command("sudo rm -rf /"))

    def test_rm_rf_normal_path_still_blocked_by_policy(self):
        # Current hook policy treats any rm with both recursive+force as dangerous.
        self.assertTrue(pre_tool_use.is_dangerous_rm_command("rm -rf ./node_modules"))


if __name__ == "__main__":
    unittest.main()
