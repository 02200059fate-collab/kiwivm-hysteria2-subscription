# Security Policy

## Reporting

请勿在公开 Issue、Discussion、截图或日志中提交以下内容：

- KiwiVM VEID/API Key；
- Hysteria 2 URI、认证密码或证书私钥；
- 私人订阅 URL/token；
- SSH 私钥、家庭公网 IP、路由器配置或客户端数据库。

维护者发布仓库后，应在此处补充私密安全联系方式。此前请不要公开披露仍可利用的秘密。

## If a secret leaks

1. 立即撤销或轮换对应秘密。
2. 生成新的 Hysteria 认证信息或订阅 token。
3. 从 Git 历史中清除秘密，而不只是创建一个删除提交。
4. 检查服务器访问日志和 KiwiVM 用量。
5. 通知所有使用旧配置的客户端更新。

项目中的 `scripts/check-secrets.py` 只拦截常见模式，不能替代 GitHub Secret Scanning、人工审查或秘密轮换。
