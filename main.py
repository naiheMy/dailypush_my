import requests
import json
import datetime
import pymysql
from config import DB_CONFIG, API_KEYS, API_URLS, DEBUG

# 定义默认值，当API调用失败时使用
def get_default_weather_info():
    return {
        'city': '未知',
        'date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'day': '未知',
        'weather': '数据获取失败',
        'temp': '未知',
        'feelsLike': '未知',
        'highTemp': '未知',
        'lowTemp': '未知',
        'rh': '未知',
        'wind': '未知'
    }

def get_default_history_events():
    return ['历史数据获取失败，请稍后再试']

def get_default_hot_searches():
    return [{'title': '热搜数据获取失败', 'hot': ''}]

def get_default_ai_advice():
    return '由于数据问题，今日暂无天气建议 (´；ω；`)'

# 动态导入cursorclass
DB_CONFIG['cursorclass'] = getattr(pymysql.cursors, DB_CONFIG['cursorclass'].split('.')[-1])

def save_to_database(push_data):
    """
    保存推送数据到数据库
    """
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 创建表（如果不存在）
            create_table_query = """
            CREATE TABLE IF NOT EXISTS daily_pushes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                push_date DATE NOT NULL,
                push_time TIME NOT NULL,
                weather_info JSON NOT NULL,
                ai_advice TEXT,
                history_events JSON NOT NULL,
                hot_searches JSON NOT NULL,
                daily_image VARCHAR(255),
                status ENUM('success', 'failed', 'pending') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_push (push_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_query)
            
            # 插入数据
            insert_query = """
            INSERT INTO daily_pushes (
                push_date, push_time, weather_info, ai_advice, 
                history_events, hot_searches, daily_image, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                push_time = VALUES(push_time),
                weather_info = VALUES(weather_info),
                ai_advice = VALUES(ai_advice),
                history_events = VALUES(history_events),
                hot_searches = VALUES(hot_searches),
                daily_image = VALUES(daily_image),
                status = VALUES(status),
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(insert_query, (
                push_data['push_date'],
                push_data['push_time'],
                push_data['weather_info'],
                push_data['ai_advice'],
                push_data['history_events'],
                push_data['hot_searches'],
                push_data['daily_image'],
                push_data['status']
            ))
        
        # 提交事务
        conn.commit()
        print(f"\n数据库操作成功: 保存了{push_data['push_date']}的推送数据")
        
    except pymysql.MySQLError as e:
        print(f"\n数据库错误: {e}")
        if hasattr(e, 'args') and len(e.args) > 1:
            print(f"  错误代码: {e.args[0]}")
            print(f"  错误信息: {e.args[1]}")
        raise
    except Exception as e:
        print(f"\n保存数据到数据库时发生未知错误: {e}")
        raise
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()
            print("数据库连接已关闭")

# 从配置文件获取API地址
message_url = API_URLS['message_url']
weather_url = API_URLS['weather_url']
history_url = API_URLS['history_url']
weibohot_url = API_URLS['weibohot_url']
ai_url = API_URLS['ai_url']
ai_api_key = API_KEYS['ai_api_key']
image_url = API_URLS['image_url']

# 记录开始时间
start_time = datetime.datetime.now()
print(f"\n===== 程序开始执行: {start_time.strftime('%Y-%m-%d %H:%M:%S')} =====")

# 初始化数据变量，设置默认值
weather_info = get_default_weather_info()
weather_info_json = json.dumps(weather_info, ensure_ascii=False)
history_events = get_default_history_events()
hot_searches = get_default_hot_searches()
daily_image = None
weather_advice = get_default_ai_advice()
all_services_status = {
    'weather': 'failed',
    'history': 'failed', 
    'hot_searches': 'failed',
    'image': 'failed',
    'ai': 'failed'
}

# 1. 获取天气信息（独立错误处理）
try:
    print("正在获取天气信息...")
    weather_response = requests.get(weather_url, timeout=10)
    print(f"天气接口状态码: {weather_response.status_code}")

    if DEBUG:
        print(f"天气接口原始响应: {weather_response.text}")

    weather_data = weather_response.json()
    print(f"天气数据解析成功，包含字段: {list(weather_data.keys())}")

    if weather_data.get("code") == 1 and 'data' in weather_data:
        weather_info = weather_data['data']
        weather_info_json = json.dumps(weather_info, ensure_ascii=False)
        all_services_status['weather'] = 'success'
        print("\n天气信息提取成功:")
        for key, value in weather_info.items():
            print(f"  {key}: {value}")
    else:
        print(f"\n天气信息获取失败: {weather_data.get('message', '未知错误')}")
except Exception as e:
    print(f"\n天气信息获取异常: {str(e)}")
    # 使用默认天气信息
    print("使用默认天气信息")

# 2. 获取历史上的今天（独立错误处理）
try:
    print("\n正在获取历史上的今天...")
    history_response = requests.get(history_url, timeout=10)
    print(f"历史接口状态码: {history_response.status_code}")

    if DEBUG:
        print(f"历史接口原始响应: {history_response.text}")

    history_data = history_response.json()
    print(f"历史数据解析成功，包含字段: {list(history_data.keys())}")

    if "data" in history_data and isinstance(history_data['data'], list):
        history_events = history_data['data']
        all_services_status['history'] = 'success'
        print(f"成功获取 {len(history_events)} 条历史事件")
    else:
        print("\n历史上的今天获取失败")
except Exception as e:
    print(f"\n历史数据获取异常: {str(e)}")
    # 使用默认历史事件
    print("使用默认历史事件")

# 3. 获取微博热搜（独立错误处理）
try:
    print("\n正在获取微博热搜...")
    weibohot_response = requests.get(weibohot_url, timeout=10)
    print(f"微博热搜接口状态码: {weibohot_response.status_code}")

    if DEBUG:
        print(f"微博热搜接口原始响应: {weibohot_response.text}")

    weibohot_data = weibohot_response.json()
    print(f"微博热搜数据解析成功，包含字段: {list(weibohot_data.keys())}")

    if "data" in weibohot_data and isinstance(weibohot_data['data'], list):
        hot_searches = weibohot_data['data'][:10]  # 只取前10条
        all_services_status['hot_searches'] = 'success'
        print(f"成功获取 {len(hot_searches)} 条微博热搜")
        if DEBUG and hot_searches:
            print(f"前5条热搜示例: {hot_searches[:5]}")
    else:
        print("\n微博热搜获取失败")
except Exception as e:
    print(f"\n微博热搜获取异常: {str(e)}")
    # 使用默认热搜
    print("使用默认热搜数据")

# 4. 获取每日一图（独立错误处理）
try:
    print("\n正在获取每日一图...")
    # 添加请求头以避免403错误
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    image_response = requests.get(image_url, headers=headers, timeout=10)
    print(f"图片接口状态码: {image_response.status_code}")

    if image_response.status_code == 200:
        # 解析JSON响应
        image_data = image_response.json()
        if DEBUG:
            print(f"图片数据解析成功，包含字段: {list(image_data.keys())}")
        
        # 从JSON中提取图片链接
        daily_image = image_data.get('image_links')
        if daily_image:
            all_services_status['image'] = 'success'
            print(f"成功获取每日图片URL: {daily_image}")
        else:
            print("\n图片数据中未找到有效图片链接")
    else:
        print("\n每日一图获取失败")
except Exception as e:
    print(f"\n每日一图获取异常: {str(e)}")
    # 保持daily_image为None

# 5. 调用AI生成天气建议（独立错误处理）
try:
    # 只有在天气数据获取成功时才调用AI
    if all_services_status['weather'] == 'success':
        print("\n正在生成天气建议...")
        print(f"AI请求URL: {ai_url}")

        ai_payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "请根据以下天气数据，生成一段100字以内的天气建议。"
                        "请使用动漫《魔女之旅》中伊蕾娜的语气——优雅、自信、略带傲娇、偶尔可爱，"
                        "像在对旅客轻松说话一样。可以加入少量可爱的颜文字，例如 (⌒‿⌒)・(〃´-`〃)・(*´ω`*)・(>ω<)。"
                        "内容包括：是否适合外出活动、天气状况点评、穿衣提醒。"
                        f"天气数据：{json.dumps(weather_info, ensure_ascii=False)}"
                    )
                }
            ]
        }

        if DEBUG:
            print(f"AI请求payload: {json.dumps(ai_payload, ensure_ascii=False, indent=2)}")

        ai_headers = {
            "Authorization": f"Bearer {ai_api_key}",
            "Content-Type": "application/json"
        }

        ai_response = requests.post(ai_url, json=ai_payload, headers=ai_headers, timeout=30)
        print(f"AI接口状态码: {ai_response.status_code}")

        if DEBUG:
            print(f"AI接口原始响应: {ai_response.text}")

        ai_result = ai_response.json()
        print(f"AI响应解析成功，包含字段: {list(ai_result.keys())}")

        if "choices" in ai_result and ai_result["choices"]:
            weather_advice = ai_result["choices"][0]["message"]["content"]
            all_services_status['ai'] = 'success'
            print(f"\nAI天气建议生成成功:")
            print(f"{weather_advice}")
        else:
            print("\nAI响应格式异常，无法提取内容")
            weather_advice = get_default_ai_advice()
    else:
        print("\n天气数据获取失败，跳过AI建议生成")
except Exception as e:
    print(f"\nAI建议生成异常: {str(e)}")
    # 使用默认天气建议
    print("使用默认天气建议")

# 准备要存储的数据
push_data = {
    'push_date': datetime.datetime.now().strftime('%Y-%m-%d'),
    'push_time': datetime.datetime.now().strftime('%H:%M:%S'),
    'weather_info': weather_info_json,
    'ai_advice': weather_advice,
    'history_events': json.dumps(history_events, ensure_ascii=False),
    'hot_searches': json.dumps(hot_searches, ensure_ascii=False),
    'daily_image': daily_image,
    'status': 'pending'  # 初始状态
}

print("\n各服务状态汇总:")
for service, status in all_services_status.items():
    print(f"  {service}: {'✓ 成功' if status == 'success' else '✗ 失败'}")
    
    # 构建结构化的天气内容
    # 根据天气服务状态添加提示信息
    weather_status_note = """
            <div style="margin-bottom: 10px; padding: 8px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;">
                <strong>⚠️ 提示：</strong>天气数据获取失败，以下为默认信息
            </div>
    """ if all_services_status['weather'] != 'success' else ""
    
    # 为天气建议添加状态提示
    ai_status_note = """
                <span style="color: #856404; font-size: 0.9em; margin-left: 10px;">(数据缺失，默认建议)</span>
    """ if all_services_status['ai'] != 'success' else ""
    
    weather_html = f"""
            <h2>🌤️ 今日天气</h2>
            {weather_status_note}
            <div style="margin-left: 20px; background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">城市：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('city', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">日期：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('date', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">星期：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('day', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">天气状况：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('weather', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">温度：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('temp', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">体感温度：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('feelsLike', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">最高气温：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('highTemp', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">最低气温：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('lowTemp', '未知')}℃</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">相对湿度：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('rh', '未知')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #dee2e6;">
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">风力风向：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_info.get('wind', '未知')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; width: 30%; font-weight: bold; color: #495057;">💡 天气建议：</td>
                        <td style="padding: 8px 0; color: #212529;">{weather_advice}{ai_status_note}</td>
                    </tr>
                </table>
            </div>
"""

    # 生成HTML格式的内容
    final_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>伊蕾娜的每日播报</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            font-size: 16px;
        }
        .container {
            background-color: #fff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin: 10px;
        }
        h1 {
            color: #4a6fa5;
            text-align: center;
            border-bottom: 2px solid #4a6fa5;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        h2 {
            color: #6b8e23;
            margin-top: 20px;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #6b8e23;
            font-size: 1.3em;
        }
        /* 响应式设计 */
        @media (min-width: 600px) {
            .container {
                max-width: 800px;
                margin: 20px auto;
                padding: 25px;
            }
        }
        /* 确保表格在移动端友好显示 */
        table {
            width: 100%;
            font-size: 0.9em;
        }
        /* 确保图片在移动端正确缩放 */
        img {
            max-width: 100%;
            height: auto;
        }
        p {
            margin-bottom: 15px;
            text-align: justify;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin-bottom: 8px;
        }
        .weather-section {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            word-break: break-word;
        }
        .history-section {
            background-color: #f0f8ff;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            word-break: break-word;
        }
        .hot-section {
            background-color: #fff8e1;
            padding: 15px;
            border-radius: 8px;
            word-break: break-word;
        }
        .hot-item {
            padding: 8px 0;
            border-bottom: 1px solid #f5deb3;
            word-break: break-word;
        }
        .hot-item:last-child {
            border-bottom: none;
        }
        .hot-rank {
            font-weight: bold;
            color: #d32f2f;
            margin-right: 10px;
        }
        .hot-title {
            font-weight: 500;
            display: inline-block;
            max-width: 70%;
        }
        .hot-count {
            color: #757575;
            font-size: 0.85em;
            margin-left: 10px;
            white-space: nowrap;
        }
        /* 移动端优化样式 */
        @media (max-width: 480px) {
            h1 {
                font-size: 1.3em;
            }
            h2 {
                font-size: 1.1em;
                margin-top: 15px;
            }
            .container {
                padding: 10px;
                margin: 5px;
            }
            .weather-section, .history-section, .hot-section {
                padding: 10px;
            }
            table td {
                padding: 6px 0;
                font-size: 0.85em;
            }
            .hot-item {
                padding: 6px 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>伊蕾娜的每日播报</h1>
        
        <div class="weather-section">
'''

    # 添加结构化的天气内容
    final_content += weather_html

    final_content += '''
        </div>
        
        <div class="history-section">
            <h2>📜 历史上的今天</h2>
            <ul>
'''

    # 添加历史上的今天内容
    # 根据历史服务状态添加提示信息
    if all_services_status['history'] != 'success':
        final_content += "            <div style='margin-bottom: 10px; padding: 8px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;'>\n"
        final_content += "                <strong>⚠️ 提示：</strong>历史数据获取失败\n"
        final_content += "            </div>\n"
    
    # 使用卡片式设计显示历史事件
    final_content += "            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef;'>\n"
    
    if history_events:
        for event in history_events:
            final_content += "                <div style='padding: 10px; margin-bottom: 8px; background-color: white; border-radius: 6px; border-left: 4px solid #007bff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>\n"
            final_content += f"                    {event}\n"
            final_content += "                </div>\n"
    else:
        final_content += "                <div style='padding: 20px; text-align: center; color: #6c757d;'>\n"
        final_content += "                    暂无历史事件数据\n"
        final_content += "                </div>\n"
    
    final_content += "            </div>\n"

    final_content += '''
            </ul>
        </div>
        
        <div class="hot-section">
            <h2>🔥 微博热搜</h2>
'''

    # 添加微博热搜内容
    # 根据热搜服务状态添加提示信息
    if all_services_status['hot_searches'] != 'success':
        final_content += "            <div style='margin-bottom: 10px; padding: 8px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;'>\n"
        final_content += "                <strong>⚠️ 提示：</strong>热搜数据获取失败\n"
        final_content += "            </div>\n"
    
    # 使用统一的div结构替代class样式，确保在各种邮件客户端中显示一致
    final_content += "            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef;'>\n"
    
    if hot_searches:
        for i, hot in enumerate(hot_searches, 1):
            # 设置排名背景色
            rank_color = '#ff4757' if i <= 3 else '#ff6b81'
            
            final_content += "                <div style='display: flex; align-items: center; padding: 12px; margin-bottom: 8px; background-color: white; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>\n"
            final_content += f"                    <div style='width: 24px; height: 24px; line-height: 24px; text-align: center; background-color: {rank_color}; color: white; border-radius: 4px; margin-right: 10px; font-weight: bold; font-size: 14px;'>{i}</div>\n"
            
            if isinstance(hot, dict):
                title = hot.get('title', '未知标题')
                hot_count = hot.get('hot', '')
                final_content += f"                    <div style='flex: 1; color: #212529; font-size: 14px; line-height: 1.5;'>{title}</div>\n"
                if hot_count:
                    final_content += f"                    <div style='color: #6c757d; font-size: 12px; margin-left: 10px;'>{hot_count}</div>\n"
            else:
                final_content += f"                    <div style='flex: 1; color: #212529; font-size: 14px; line-height: 1.5;'>{hot}</div>\n"
            
            final_content += "                </div>\n"
    else:
        final_content += "                <div style='padding: 20px; text-align: center; color: #6c757d;'>\n"
        final_content += "                    暂无热搜数据\n"
        final_content += "                </div>\n"
    
    final_content += "            </div>\n"

    final_content += '''
        </div>
        
        <div style="margin-top: 30px;">
            <h2>🖼️ 每日一图</h2>
            <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">'''
    
    # 根据图片服务状态添加内容
    if daily_image:
        final_content += f"                <img src=\"{daily_image}\" alt=\"每日一图\" style=\"max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 3px solid white;\">\n"
    else:
        final_content += "                <div style='padding: 50px 20px; background-color: white; border: 1px dashed #dee2e6; border-radius: 8px; display: inline-block;'>\n"
        final_content += "                    <p style='color: #6c757d; font-size: 18px; margin: 0;'>图片获取失败 </p>\n"
        final_content += "                    <p style='color: #adb5bd; font-size: 14px; margin: 5px 0 0;'>(┬＿┬)</p>\n"
        final_content += "                </div>\n"
    
    final_content += '''            </div>
        </div>'''

    # 添加页脚信息，包含数据缺失提示
    service_status_text = "\n"
    failed_services = [service for service, status in all_services_status.items() if status != 'success']
    
    if failed_services:
        service_status_text += "            <p style='margin: 10px 0; color: #856404; font-size: 13px;'>\n"
        service_status_text += "                <strong>⚠️ 今日数据状态提示：</strong>\n"
        
        status_map = {
            'weather': '天气数据',
            'history': '历史事件',
            'hot_searches': '热搜榜',
            'image': '每日一图',
            'ai': '天气建议'
        }
        
        failed_texts = [status_map.get(s, s) for s in failed_services]
        service_status_text += f"                以下服务暂时不可用：{', '.join(failed_texts)}\n"
        service_status_text += "                数据将在系统恢复后自动补充，感谢您的理解！\n"
        service_status_text += "            </p>\n"
    
    final_content += '''
        <div style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-top: 1px solid #dee2e6; border-radius: 8px; text-align: center; color: #6c757d; font-size: 14px;">
            <p>✨ 伊蕾娜的每日播报 ✨</p>
            <p>数据更新时间：'''
    final_content += datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_content += '''</p>'''
    final_content += service_status_text
    final_content += '''
            <p style="margin-top: 15px; font-size: 12px; color: #adb5bd;">若您发现内容有误或有建议，请随时反馈</p>
        </div>
    </div>
</body>
</html>'''

    print("\n正在构建HTML内容...")
    print(f"HTML内容长度: {len(final_content)} 字符")
    print(
        f"内容包含: 天气信息{'(默认)' if all_services_status['weather'] != 'success' else ''}、"
        f"{len(history_events)}条历史事件{'(默认)' if all_services_status['history'] != 'success' else ''}、"
        f"{len(hot_searches)}条热搜{'(默认)' if all_services_status['hot_searches'] != 'success' else ''}、"
        f"{'图片' if daily_image else '无图片'}")

# 发送消息到pushplus（独立错误处理）
try:
    print("\n正在发送到pushplus...")
    message_payload = {
        "token": API_KEYS['pushplus_token'],
        "title": "伊蕾娜的每日播报",
        "content": final_content,
        "channel": "mail"
    }

    if DEBUG:
        print(f"pushplus请求payload: {json.dumps(message_payload, ensure_ascii=False)[:500]}...")

    message_response = requests.post(message_url, json=message_payload, timeout=30)
    print(f"pushplus接口状态码: {message_response.status_code}")
    print(f"pushplus响应: {message_response.text}")

    if message_response.headers.get('content-type') == 'application/json':
        push_result = message_response.json()
        print(f"pushplus响应解析成功，包含字段: {list(push_result.keys())}")
        if push_result.get("code") == 200:
            print("\n任务完成！")
            push_data['status'] = 'success'
        else:
            print(f"\npushplus发送失败: {push_result.get('msg', '未知错误')}")
            push_data['status'] = 'failed'
    else:
        print("\npushplus响应格式异常")
        push_data['status'] = 'failed'
except Exception as e:
    print(f"\n推送消息异常: {str(e)}")
    push_data['status'] = 'failed'

# 无论推送结果如何，都保存数据到数据库
try:
    save_to_database(push_data)
    print(f"\n数据已成功保存到数据库！状态: {push_data['status']}")
except Exception as db_error:
    print(f"\n数据库保存失败: {db_error}")

# 计算总执行时间并结束
end_time = datetime.datetime.now()
total_time = end_time - start_time
print(f"\n===== 程序执行完毕: {end_time.strftime('%Y-%m-%d %H:%M:%S')} =====")
print(f"总执行时间: {total_time.total_seconds():.2f} 秒")

# 输出服务状态汇总
print("\n===== 服务状态汇总 =====")
success_count = sum(1 for status in all_services_status.values() if status == 'success')
failed_count = len(all_services_status) - success_count
print(f"成功服务数: {success_count}/{len(all_services_status)}")
print(f"失败服务数: {failed_count}/{len(all_services_status)}")
for service, status in all_services_status.items():
    print(f"  {service}: {'✓ 成功' if status == 'success' else '✗ 失败'}")
print("\n推送状态: {'✓ 成功' if push_data['status'] == 'success' else '✗ 失败'}")
print("==================================================")
