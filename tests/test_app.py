import base64
import tempfile
import unittest
import urllib.parse
from pathlib import Path

from server import app


class SubscriptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        app.CONFIG_DIR = Path(self.temporary.name)
        app.DISPLAY_TIMEZONE = "Asia/Shanghai"
        values = {
            "node_uri": "hysteria2://example-secret@192.0.2.1:443/?insecure=1#old",
            "node_name": "Example",
            "country_emoji": "🇺🇸",
            "token": "test-token",
        }
        for name, value in values.items():
            (app.CONFIG_DIR / name).write_text(value, encoding="utf-8")

    def test_build_subscription_renames_without_exposing_old_fragment(self):
        body, used, total = app.build_subscription(
            {
                "total": 100_000_000_000,
                "used": 25_000_000_000,
                "reset": 1_799_999_999,
            }
        )
        uri = base64.b64decode(body).decode("utf-8").strip()
        label = urllib.parse.unquote(urllib.parse.urlsplit(uri).fragment)
        self.assertEqual(used, 25_000_000_000)
        self.assertEqual(total, 100_000_000_000)
        self.assertIn("🇺🇸 Example｜余75.0G", label)
        self.assertNotIn("#old", uri)

    def test_unknown_path_is_not_the_private_endpoint(self):
        expected = "/sub/" + app.read_value("token")
        self.assertEqual(expected, "/sub/test-token")
        self.assertNotEqual(expected, "/sub/wrong-token")


if __name__ == "__main__":
    unittest.main()
