import unittest

from src.validation import parse_models
from src.validation import positive_int
from src.validation import validate_allowed_cidrs
from src.validation import validate_instance_type
from src.validation import validate_log_retention


class ValidationTests(unittest.TestCase):
    def test_accepts_specific_ipv4_cidrs(self) -> None:
        self.assertEqual(
            validate_allowed_cidrs(["203.0.113.10/32", "198.51.100.0/24"]),
            ["203.0.113.10/32", "198.51.100.0/24"],
        )

    def test_rejects_unsafe_or_invalid_allowlists(self) -> None:
        invalid_values = [
            [],
            "203.0.113.10/32",
            ["0.0.0.0/0"],
            ["2001:db8::/32"],
            ["203.0.113.10"],
            ["203.0.113.10/24"],
            [123],
        ]
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_allowed_cidrs(value)

    def test_parses_models(self) -> None:
        self.assertEqual(parse_models(None), ["llama3.2:latest"])
        self.assertEqual(parse_models("qwen3:8b, llama3.2:latest"), ["qwen3:8b", "llama3.2:latest"])

    def test_rejects_shell_unsafe_models(self) -> None:
        for value in ("", "model name", "model;reboot", "$(reboot)"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_models(value)

    def test_validates_numeric_and_instance_settings(self) -> None:
        self.assertEqual(positive_int("size", 100, 100), 100)
        self.assertEqual(validate_instance_type("g5.2xlarge"), "g5.2xlarge")
        self.assertEqual(validate_log_retention(30), 30)
        with self.assertRaises(ValueError):
            positive_int("size", 99, 100)
        with self.assertRaises(ValueError):
            validate_instance_type("g5.2xlarge;bad")
        with self.assertRaises(ValueError):
            validate_log_retention(31)


if __name__ == "__main__":
    unittest.main()
