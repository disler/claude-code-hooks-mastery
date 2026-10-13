"""Regression tests for the rm guard in pre_tool_use.py (issue #28).

Run:  python test_pre_tool_use.py
Covers the reported false positive (a `-r` substring inside a pathname must
never read as the recursive flag) plus the true positives the old regex
caught, so the fix cannot silently disarm the guard.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pre_tool_use import is_dangerous_rm_command


class TestIsDangerousRmCommand(unittest.TestCase):
    def assertBlocked(self, command):
        self.assertTrue(is_dangerous_rm_command(command), f"should block: {command}")

    def assertAllowed(self, command):
        self.assertFalse(is_dangerous_rm_command(command), f"should allow: {command}")

    def test_issue_28_pathname_substring_is_not_a_flag(self):
        self.assertAllowed(
            "rm /Users/me/project/soft-hold-enrollment/db/migrate/20251212031504_add_payment_account_to_enrollment_invoices.rb"
            " /Users/me/project/soft-hold-enrollment/db/migrate/foobar.rb"
        )

    def test_plain_rm_is_allowed(self):
        self.assertAllowed("rm file.txt")
        self.assertAllowed("rm -v old.log")
        self.assertAllowed("rm -- file-with-dash")

    def test_recursive_force_variants_are_blocked(self):
        for command in (
            "rm -rf /",
            "rm -fr /tmp/x",
            "rm -Rf ./build",
            "rm --recursive --force ./build",
            "rm --force --recursive ./build",
            "rm -r ./build -f",
            "rm -f ./build -r",
            "sudo rm -rf /",
        ):
            self.assertBlocked(command)

    def test_recursive_into_dangerous_targets_is_blocked(self):
        for command in (
            "rm -r /",
            "rm -r ~",
            "rm -r ..",
            "rm -r .",
            "rm -r /*",
            "rm --recursive $HOME/stuff",
        ):
            self.assertBlocked(command)

    def test_recursive_into_safe_target_is_allowed(self):
        self.assertAllowed("rm -r ./build")
        self.assertAllowed("rm -r /tmp/scratch-dir")

    def test_chained_commands_evaluate_each_segment(self):
        self.assertBlocked("echo done; rm -rf /")
        self.assertAllowed("echo done; rm old.log")

    def test_unparseable_command_is_not_blocked(self):
        self.assertAllowed("rm 'unbalanced quote")


if __name__ == "__main__":
    unittest.main()
