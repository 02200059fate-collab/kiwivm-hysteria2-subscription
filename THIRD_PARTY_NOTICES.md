# Third-party notices

This project links to or takes configuration-design inspiration from the
following upstream projects. It does not vendor their rule databases or
binaries.

## LingJingMaster/Shadowrocket-Rules

- Source: <https://github.com/LingJingMaster/Shadowrocket-Rules>
- License: MIT
- Use here: reference for Shadowrocket DNS leak prevention, private-network
  exclusions, DNS hijacking and HTTPDNS handling. Multi-region policy groups,
  banking rules, MITM and URL rewrites are intentionally not copied.

## blackmatrix7/ios_rule_script

- Source: <https://github.com/blackmatrix7/ios_rule_script>
- License: GPL-2.0
- Use here: client configurations reference the upstream-hosted Shadowrocket
  `ChinaMax` and `BlockHttpDNS` lists by URL. The lists are not redistributed.

## MetaCubeX/meta-rules-dat

- Source: <https://github.com/MetaCubeX/meta-rules-dat>
- License: GPL-3.0
- Use here: Mihomo downloads the upstream release assets at runtime. The data
  files are not redistributed.

## Hysteria 2 and Caddy

- Hysteria 2: <https://github.com/apernet/hysteria>
- Caddy: <https://github.com/caddyserver/caddy>
- Use here: installed from their official distribution channels; binaries are
  not committed to this repository.
