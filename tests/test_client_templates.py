from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ShadowrocketTemplateTests(unittest.TestCase):
    def test_douyin_has_an_explicit_direct_rule(self):
        config = (ROOT / "client" / "shadowrocket-auto-route.conf").read_text(
            encoding="utf-8"
        )
        expected = (
            "RULE-SET,https://raw.githubusercontent.com/blackmatrix7/"
            "ios_rule_script/master/rule/Shadowrocket/DouYin/DouYin.list,DIRECT"
        )
        self.assertIn(expected, config)
        self.assertLess(config.index(expected), config.index("ChinaMax.list,DIRECT"))

    def test_httpdns_is_direct_instead_of_rejected(self):
        config = (ROOT / "client" / "shadowrocket-auto-route.conf").read_text(
            encoding="utf-8"
        )
        expected = (
            "RULE-SET,https://raw.githubusercontent.com/blackmatrix7/"
            "ios_rule_script/release/rule/Shadowrocket/BlockHttpDNS/"
            "BlockHttpDNS.list,DIRECT"
        )
        self.assertIn(expected, config)
        self.assertNotRegex(config, r"BlockHttpDNS\.list,REJECT")


if __name__ == "__main__":
    unittest.main()
