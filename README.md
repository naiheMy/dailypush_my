# 伊蕾娜的每日播报 🧙‍♀️

基于 Python 的每日信息推送脚本
以《魔女之旅》伊蕾娜的 傲娇 + 优雅 风格生成 AI 天气建议，并整合天气、历史上的今天、微博热搜、每日一图等信息，通过 PushPlus 推送至邮箱 / 微信等渠道，支持 MySQL 存储推送记录，开箱即用！

## ✨ 功能亮点

📅 多维度信息整合：天气、历史上的今天、微博热搜、每日一图，一次推送全搞定

🧠 AI 个性化建议：基于 GPT-3.5-Turbo 生成伊蕾娜风天气建议（傲娇 × 优雅 × 可爱颜文字）

📤 多渠道推送：PushPlus 支持邮箱 / 微信 / 企业微信 / 钉钉等

💾 数据持久化：MySQL 自动存储每日推送记录，避免重复推送，便于历史追溯

🎨 精美排版：HTML 排版适配移动端与 PC

🚀 易配置：配置文件集中管理，不需改动主代码

## 📋 环境准备
### 1. 系统环境

Python 3.7+

MySQL 5.7+/8.0+

### 2. 安装依赖
pip install requests pymysql

## ⚙️ 配置步骤
### 1. 准备配置文件

仓库提供 config.example.py 模板，执行以下命令复制为项目专用配置：

cp config.example.py config.py


👉 注意：config.py 已加入 .gitignore，避免敏感信息上传到仓库。

### 2. 填写配置信息

打开 config.py，将所有 <占位符> 替换为真实信息。

配置项分类	参数	说明
数据库配置	host / user / password / database	填写你的 MySQL 信息，需提前创建空库（如 daily_push）
AI 密钥	ai_api_key	ChatAnywhere 的 GPT-3.5 API Key
PushPlus	pushplus_token	PushPlus → 一对一推送 → Token
接口配置	weather_url	替换 districtId（示例：河南省郑州市中牟县）

⚠ 切勿将 config.py 提交到仓库！里面包含 API Key / 数据库密码等敏感内容。

## 🚀 运行脚本

配置完成后直接运行主脚本：

python main.py


推送成功后，你将在邮箱或微信收到精美排版的每日播报。

## ⏰ 定时自动运行
### Linux/macOS（Crontab）
crontab -e


添加示例（每天早上 8 点执行）：

0 8 * * * /usr/bin/python3 /你的路径/main.py >> /你的路径/push.log 2>&1

### Windows（任务计划程序）

创建批处理文件 run_push.bat：

@echo off
python "C:\你的路径\main.py"
pause


任务计划程序 → 创建基本任务 → 选择每日执行。

## 📦 接口说明
功能	来源	备注
天气信息	dwo.cc 天气 API	免费，需修改 districtId
历史上的今天	api-m.com	免费
微博热搜	api-m.com	免费
AI 建议	ChatAnywhere（GPT-3.5）	需申请 API Key
每日一图	img.8845.top	免费图片 API
推送服务	PushPlus	免费使用
## ❗ 注意事项

敏感信息防护：请勿将含密钥的 config.py 上传到仓库

接口稳定性：公开 API 偶尔会失效，异常时查看日志

AI 调用额度：ChatAnywhere 需自行查看额度情况

数据库权限：确保 MySQL 用户有建表、插入、更新权限

天气地区参数：务必使用正确的 districtId

## 🎨 效果预览
![](https://cdn.jsdelivr.net/gh/naiheMy/my_imgs@img/img/202511301242879.png)

## 📄 许可证

本项目基于 MIT License 开源，支持修改、分发与商用。
详情见 LICENSE 文件。

## 📞 反馈与贡献

如果使用过程中遇到问题，欢迎：

在 Issues 中提交反馈

提交 Pull Request 改进代码或添加功能
