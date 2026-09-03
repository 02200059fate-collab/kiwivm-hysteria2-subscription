from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ShadowrocketTemplateTests(unittest.TestCase):
    def test_douyin_and_bytedance_have_compact_direct_fallbacks(self):
        config = (ROOT / "client" / "shadowrocket-auto-route.conf").read_text(
            encoding="utf-8"
        )
        douyin = (
            "RULE-SET,https://raw.githubusercontent.com/blackmatrix7/"
            "ios_rule_script/master/rule/Shadowrocket/DouYin/DouYin.list,DIRECT"
        )
        bytedance = (
            "RULE-SET,https://raw.githubusercontent.com/blackmatrix7/"
            "ios_rule_script/master/rule/Shadowrocket/ByteDance/"
            "ByteDance.list,DIRECT"
        )
        china_ips_bgp = (
            "RULE-SET,https://raw.githubusercontent.com/blackmatrix7/"
            "ios_rule_script/master/rule/Shadowrocket/ChinaIPsBGP/"
            "ChinaIPsBGP.list,DIRECT"
        )
        block_httpdns = "BlockHttpDNS.list,DIRECT"

        for expected in (douyin, bytedance, china_ips_bgp):
            self.assertIn(expected, config)
        self.assertLess(config.index(douyin), config.index(bytedance))
        self.assertLess(config.index(bytedance), config.index(china_ips_bgp))
        self.assertLess(config.index(china_ips_bgp), config.index(block_httpdns))

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
        self.assertNotIn("DOMAIN,httpdns.volcengineapi.com,REJECT", config)


if __name__ == "__main__":
    unittest.main()
