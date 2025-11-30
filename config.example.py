# ==================== 每日播报脚本 - 配置文件模板 ====================
# 使用说明：
# 1. 复制此文件并重命名为 config.py
# 2. 将下方所有 <占位符> 替换为你的真实信息
# 3. config.py 已加入 .gitignore，请勿提交到仓库！
# 4. 敏感信息（密码/API Key/Token）务必妥善保管，切勿公开分享

# -------------------------- 数据库配置 --------------------------
# 说明：需提前创建 MySQL 数据库（推荐库名 daily_push），确保数据库用户有建表/读写权限
DB_CONFIG = {
    'host': '<你的数据库主机IP/域名>',          # 示例：127.0.0.1
    'user': '<数据库用户名>',                  # 示例：root
    'password': '<数据库密码>',                # 示例：your_mysql_password123
    'database': '<数据库名>',                  # 示例：daily_push（脚本会自动创建表）
    'charset': 'utf8mb4',                     # 固定值，无需修改
    'cursorclass': 'pymysql.cursors.DictCursor'  # 固定值，无需修改
}

# -------------------------- API密钥配置 --------------------------
# AI API Key 获取：https://chatanywhere.tech/（注册后可获取免费额度）
# PushPlus Token 获取：https://www.pushplus.plus/（注册后在「一对一推送」中查看）
API_KEYS = {
    'ai_api_key': '<你的ChatAnywhere API Key>',  # 示例：sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    'pushplus_token': '<你的PushPlus Token>'     # 示例：8b3cc41b86b943029a3da269c15a4ad4
}

# -------------------------- API接口配置 --------------------------
# 根据需要替换为自己的接口，或调整地区/参数
# API接口均来自https://api.aa1.cn AI接口来自https://github.com/chatanywhere/GPT_API_free
API_URLS = {
    # PushPlus 推送接口（固定值，无需修改）
    'message_url': 'https://www.pushplus.plus/send',
    # 天气接口：替换 districtId 为你的地区（格式：省份城市区县，示例：浙江省杭州市）
    # 天气接口文档：可参考 dwo.cc 官方说明
    'weather_url': 'https://api.dwo.cc/api/tianqi?districtId=<你的地区，如：浙江省杭州市>',
    # 历史上的今天接口（固定值，无需修改）
    'history_url': 'https://v2.api-m.com/api/history',
    # 微博热搜接口（固定值，无需修改）
    'weibohot_url': 'https://v2.api-m.com/api/weibohot',
    # AI 接口（ChatAnywhere GPT-3.5 接口，固定值，无需修改）
    'ai_url': 'https://api.chatanywhere.tech/v1/chat/completions',
    # 每日一图接口（固定值，无需修改）
    'image_url': 'https://img.8845.top/good'
}

# -------------------------- 日志配置 --------------------------
# DEBUG=True：输出详细调试信息（开发/排查问题用）
# DEBUG=False：仅输出关键信息（生产环境用）
DEBUG = True  # 可选值：True / False