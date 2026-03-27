# DPDNS 自动续期 - 使用 DrissionPage
FROM python:3.11-slim-bookworm

# 使用国内镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    xvfb \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 使用国内 PyPI 镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir requests DrissionPage

# 设置工作目录
WORKDIR /app

# 复制脚本
COPY dpdns_renew_drission.py /app/
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# 环境变量
ENV EMAIL=""
ENV PASSWORD=""
ENV DOMAIN="youseeicanfly.dpdns.org"
ENV AUTO_MODE="true"
ENV DISPLAY=:99

# 使用自定义入口
ENTRYPOINT ["/app/entrypoint.sh"]
