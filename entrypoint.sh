#!/bin/bash

# DPDNS 续期容器入口脚本

echo "开始运行 DPDNS 续期脚本..."

# 检测使用哪个脚本
if [ -f "/app/dpdns_renew_drission.py" ]; then
    SCRIPT="/app/dpdns_renew_drission.py"
elif [ -f "/app/dpdns_renew_selenium.py" ]; then
    SCRIPT="/app/dpdns_renew_selenium.py"
elif [ -f "/app/dpdns_renew_docker.py" ]; then
    SCRIPT="/app/dpdns_renew_docker.py"
else
    echo "错误：找不到续期脚本"
    exit 1
fi

# 使用 xvfb-run 运行脚本
xvfb-run -a --server-args="-screen 0 1920x1080x24 -ac +extension GLX +render -noreset" python3 "$SCRIPT"

# 保存退出码
EXIT_CODE=$?

# 如果设置了 AUTO_MODE，保持容器运行（用于定时任务）
if [ "$AUTO_MODE" = "true" ] && [ "$EXIT_CODE" -eq 0 ]; then
    echo "续期完成，容器保持运行（可通过 crontab 设置定时任务）"
    # 保持容器运行
    tail -f /dev/null
else
    # 直接退出
    exit $EXIT_CODE
fi
