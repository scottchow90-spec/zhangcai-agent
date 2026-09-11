# 掌财智能体局域网访问

启动 `scripts/start-local.ps1`（或运行 `pnpm dev`）后，前端监听 `0.0.0.0:3001`，同一局域网设备使用本机 IPv4 地址访问：

```powershell
ipconfig
# 例如 http://192.168.31.115:3001/
```

DeepSeek Harness 桥接服务监听 `0.0.0.0:4318`。网页会根据当前访问地址自动调用同一台主机的桥接服务，局域网客户端不再把 `127.0.0.1` 误认为自己的电脑。

如果其他设备仍无法连接，请在 Windows 防火墙的“专用网络”入站规则中允许 TCP 端口 3001（网页）和 4318（Harness 桥接），或以管理员运行：

```powershell
New-NetFirewallRule -DisplayName '掌财智能体网页 3001' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 3001 -Profile Private
New-NetFirewallRule -DisplayName '掌财智能体 Harness 4318' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 4318 -Profile Private
```
