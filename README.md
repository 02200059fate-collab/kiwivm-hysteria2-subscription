# KiwiVM Hysteria 2 Dynamic Subscription

在一台干净的 Debian/Ubuntu VPS 上部署：

- Hysteria 2 服务端（UDP 443）；
- 仅本机监听的 KiwiVM 流量查询服务；
- Caddy HTTPS 私人订阅入口（TCP 443）；
- Shadowrocket 节点名称中的剩余流量和重置日期；
- Shadowrocket 与 Mihomo/Clash.Meta 的国内直连、其他流量走代理模板。

项目**不包含任何可用节点、密码、API Key、私人订阅地址或第三方二进制文件**。

## 效果

Shadowrocket 刷新订阅后，节点名称类似：

```text
🇺🇸 Bandwagon｜余1023.4G｜10-02重置
```

同时返回标准 `subscription-userinfo` 响应头，兼容能够读取订阅流量信息的客户端。

## 适用环境

- 新安装或专门用于该用途的 Debian 11+ / Ubuntu 22.04+ VPS；
- systemd；
- KiwiVM/BandwagonHost 账户的 VEID 与 API Key；
- TCP 443 和 UDP 443 均可从公网访问；
- Shadowrocket，或兼容 Hysteria 2 的 Mihomo/Clash.Meta 客户端。

安装程序会调用 Hysteria 官方安装器，并通过 Caddy 官方软件源安装 Caddy。建议先阅读脚本再执行。

## 安装

```bash
git clone https://github.com/02200059fate-collab/kiwivm-hysteria2-subscription.git
cd kiwivm-hysteria2-subscription
sudo ./install.sh
```

安装时依次输入 KiwiVM VEID 和 API Key。API Key 使用隐藏输入，不会写入命令历史。

如果 VPS 已经安装并配置了 Caddy，安装程序默认停止，避免覆盖现有网站。确认可以备份并替换现有 Caddyfile 后，才使用：

```bash
sudo ./install.sh --force-caddy
```

常用参数：

```text
--veid VALUE
--api-key-file PATH
--server-ip ADDRESS
--domain NAME
--node-name NAME
--country-emoji FLAG
--force-caddy
```

安装成功后，所有客户端秘密只写入：

```text
/root/kiwivm-hysteria2-client/credentials.txt
```

该文件权限为 `0600`。使用以下命令在服务器上读取，禁止上传或公开分享：

```bash
sudo cat /root/kiwivm-hysteria2-client/credentials.txt
```

## Shadowrocket

1. 在 Shadowrocket 右上角点击 `+`。
2. 类型选择 `Subscribe`（订阅）。
3. 粘贴安装结果文件中的 `Shadowrocket subscription` 地址。
4. 保存并刷新订阅。
5. 导入 [`client/shadowrocket-auto-route.conf`](client/shadowrocket-auto-route.conf) 并将其设为当前配置。
6. 选择动态名称节点，开启连接。

订阅地址本身等同于私人凭据。泄露后应重新生成 `/etc/kiwivm-subscription/token` 并重启服务。

## Mihomo / Clash.Meta

复制 [`client/mihomo-auto-route.example.yaml`](client/mihomo-auto-route.example.yaml)，替换以下占位符：

- `YOUR_SERVER_IP`
- `YOUR_HYSTERIA_AUTH`
- `YOUR_CERT_SHA256_FINGERPRINT`

模板默认开启 TUN、国内 IP/域名直连、其余流量走 `PROXY`。

## 服务结构

```text
Shadowrocket ──HTTPS/TCP 443──> Caddy ──127.0.0.1:18080──> subscription service
      │                                                       │
      └────────────Hysteria 2/UDP 443──────────────────────────┘
                                                              │
                                                        KiwiVM API
```

订阅服务：

- 仅监听 `127.0.0.1`；
- API Key 不进入 URL、Caddy 日志或节点内容；
- 5 分钟缓存用量数据；
- KiwiVM API 暂时不可用时，最多使用 24 小时内的缓存；
- 随机订阅路径之外的请求返回 404；
- systemd 单元启用最小权限与文件系统保护。

## 检查状态

```bash
systemctl status hysteria-server.service
systemctl status kiwivm-subscription.service
systemctl status caddy
journalctl -u kiwivm-subscription.service --no-pager -n 50
```

运行项目测试与秘密扫描：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check-secrets.py
bash -n install.sh uninstall.sh
```

## 卸载

仅移除动态订阅服务并恢复安装前的 Caddyfile：

```bash
sudo ./uninstall.sh
```

同时移除 Hysteria 及生成的客户端凭据：

```bash
sudo ./uninstall.sh --purge-hysteria
```

## 安全边界

- 本项目无法保证 IP、域名或协议永远不被限制，也无法保证任何设备永不被封禁。
- 使用前确认所在地区法律、网络服务商条款和 VPS 服务商条款。
- 不要提交 `/etc/kiwivm-subscription`、`credentials.txt`、客户端数据库、运行日志或包含二维码的截图。
- 如果秘密曾进入 Git 历史，仅删除文件不够；应立即轮换秘密并清理历史。
- 安全问题请按 [`SECURITY.md`](SECURITY.md) 私下报告，不要在公开 Issue 中粘贴配置。

## 上游项目

- [Hysteria 2](https://github.com/apernet/hysteria)
- [Caddy](https://github.com/caddyserver/caddy)
- [ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)（Shadowrocket 国内规则远程地址）

本仓库不重新分发这些项目的二进制文件。

## License

[MIT](LICENSE)
