#!/bin/bash
# 容器环境一键初始化脚本（模板）
# 复制为 init-env.sh 并填入实际值后使用
# 用法: cp init-env.example.sh init-env.sh && vim init-env.sh && bash init-env.sh

# === 必填项 ===
XRAY_UUID="<你的VLESS UUID>"          # VLESS 用户 ID
XRAY_SERVER="<你的服务器地址>"         # Xray 服务器域名
XRAY_PORT=544                          # Xray 服务器端口
GITHUB_USER="<你的GitHub用户名>"
GITHUB_TOKEN="<你的GitHub PAT>"        # ghp_xxxxxxxx
GIT_USER_NAME="<你的名字>"
GIT_USER_EMAIL="<你的邮箱>"

# ... 其余配置与 init-env.sh 相同
