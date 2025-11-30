import requests
import json
import datetime
import pymysql
from config import DB_CONFIG, API_KEYS, API_URLS, DEBUG

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

try:
    # 记录开始时间
    start_time = datetime.datetime.now()
    print(f"\n===== 程序开始执行: {start_time.strftime('%Y-%m-%d %H:%M:%S')} =====")

    print("正在获取天气信息...")
    weather_response = requests.get(weather_url)
    print(f"天气接口状态码: {weather_response.status_code}")

    if DEBUG:
        print(f"天气接口原始响应: {weather_response.text}")

    weather_data = weather_response.json()
    print(f"天气数据解析成功，包含字段: {list(weather_data.keys())}")

    if weather_data.get("code") != 1:
        print(f"\n天气信息获取失败: {weather_data.get('message', '未知错误')}")
        raise Exception("天气信息获取失败")

    print("\n正在获取历史上的今天...")
    history_response = requests.get(history_url)
    print(f"历史接口状态码: {history_response.status_code}")

    if DEBUG:
        print(f"历史接口原始响应: {history_response.text}")

    history_data = history_response.json()
    print(f"历史数据解析成功，包含字段: {list(history_data.keys())}")

    if "data" not in history_data:
        print("\n历史上的今天获取失败")
        raise Exception("历史上的今天获取失败")

    print(f"成功获取 {len(history_data['data'])} 条历史事件")

    print("\n正在获取微博热搜...")
    weibohot_response = requests.get(weibohot_url)
    print(f"微博热搜接口状态码: {weibohot_response.status_code}")

    if DEBUG:
        print(f"微博热搜接口原始响应: {weibohot_response.text}")

    weibohot_data = weibohot_response.json()
    print(f"微博热搜数据解析成功，包含字段: {list(weibohot_data.keys())}")

    if "data" not in weibohot_data:
        print("\n微博热搜获取失败")
        raise Exception("微博热搜获取失败")

    print(f"成功获取 {len(weibohot_data['data'])} 条微博热搜")
    if DEBUG and weibohot_data['data']:
        print(f"前5条热搜示例: {weibohot_data['data'][:5]}")

    print("\n正在获取每日一图...")
    image_response = requests.get(image_url)
    print(f"图片接口状态码: {image_response.status_code}")

    if image_response.status_code == 200:
        # 新API直接返回图片，所以URL本身就是图片地址
        daily_image = image_url
        print(f"成功获取每日图片URL: {daily_image}")
    else:
        print("\n每日一图获取失败")
        daily_image = None

    # 直接从天气数据中提取信息
    weather_info = weather_data['data']

    # 直接从天气数据中提取信息
    weather_info = weather_data['data']
    print("\n天气信息提取成功:")
    for key, value in weather_info.items():
        print(f"  {key}: {value}")

    # 调用AI生成天气建议
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

    ai_response = requests.post(ai_url, json=ai_payload, headers=ai_headers)
    print(f"AI接口状态码: {ai_response.status_code}")

    if DEBUG:
        print(f"AI接口原始响应: {ai_response.text}")

    ai_result = ai_response.json()
    print(f"AI响应解析成功，包含字段: {list(ai_result.keys())}")

    if "choices" not in ai_result or not ai_result["choices"]:
        print("\nAI响应格式异常，无法提取内容")
        weather_advice = "暂无天气建议"
    else:
        weather_advice = ai_result["choices"][0]["message"]["content"]
        print(f"\nAI天气建议生成成功:")
        print(f"{weather_advice}")

    # 准备要存储的数据
    push_data = {
        'push_date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'push_time': datetime.datetime.now().strftime('%H:%M:%S'),
        'weather_info': json.dumps(weather_info, ensure_ascii=False),
        'ai_advice': weather_advice,
        'history_events': json.dumps(history_data.get('data', []), ensure_ascii=False),
        'hot_searches': json.dumps(weibohot_data.get('data', [])[:10], ensure_ascii=False),
        'daily_image': daily_image,
        'status': 'pending'  # 初始状态
    }
    
    # 构建结构化的天气内容
    weather_html = f"""
            <h2>🌤️ 今日天气</h2>
            <div style="margin-left: 20px;">
                <p><strong>城市：</strong>{weather_info.get('city', '未知')}</p>
                <p><strong>日期：</strong>{weather_info.get('date', '未知')}</p>
                <p><strong>星期：</strong>{weather_info.get('day', '未知')}</p>
                <p><strong>天气状况：</strong>{weather_info.get('weather', '未知')}</p>
                <p><strong>温度：</strong>{weather_info.get('temp', '未知')}</p>
                <p><strong>体感温度：</strong>{weather_info.get('feelsLike', '未知')}</p>
                <p><strong>最高气温：</strong>{weather_info.get('highTemp', '未知')}</p>
                <p><strong>最低气温：</strong>{weather_info.get('lowTemp', '未知')}℃</p>
                <p><strong>相对湿度：</strong>{weather_info.get('rh', '未知')}</p>
                <p><strong>风力风向：</strong>{weather_info.get('wind', '未知')}</p>
                <p><strong>💡 天气建议：</strong>{weather_advice}</p>
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
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: #fff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #4a6fa5;
            text-align: center;
            border-bottom: 2px solid #4a6fa5;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            color: #6b8e23;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-left: 10px;
            border-left: 4px solid #6b8e23;
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
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }
        .history-section {
            background-color: #f0f8ff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }
        .hot-section {
            background-color: #fff8e1;
            padding: 20px;
            border-radius: 8px;
        }
        .hot-item {
            padding: 8px 0;
            border-bottom: 1px solid #f5deb3;
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
        }
        .hot-count {
            color: #757575;
            font-size: 0.9em;
            margin-left: 10px;
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
    for event in history_data.get("data", []):
        final_content += f"            <li>{event}</li>\n"

    final_content += '''
            </ul>
        </div>
        
        <div class="hot-section">
            <h2>🔥 微博热搜</h2>
'''

    # 添加微博热搜内容
    for i, hot in enumerate(weibohot_data.get("data", [])[:10], 1):
        if isinstance(hot, dict):
            title = hot.get('title', '未知标题')
            hot_count = hot.get('hot', '')
            final_content += f"            <div class='hot-item'>\n"
            final_content += f"                <span class='hot-rank'>{i}.</span>\n"
            final_content += f"                <span class='hot-title'>{title}</span>\n"
            if hot_count:
                final_content += f"                <span class='hot-count'>{hot_count}</span>\n"
            final_content += f"            </div>\n"
        else:
            final_content += f"            <div class='hot-item'>\n"
            final_content += f"                <span class='hot-rank'>{i}.</span>\n"
            final_content += f"                <span class='hot-title'>{hot}</span>\n"
            final_content += f"            </div>\n"

    final_content += '''
        </div>
        
        <div class="image-section" style="margin-top: 30px;">
            <h2>🖼️ 每日一图</h2>
            <div style="text-align: center; padding: 20px;">
                <img src="{}" alt="每日一图" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            </div>
        </div>
    </div>
</body>
</html>'''.format(daily_image if daily_image else '')

    print("\n正在构建HTML内容...")
    print(f"HTML内容长度: {len(final_content)} 字符")
    print(
        f"内容包含: 天气信息、{len(history_data['data'])}条历史事件、{min(10, len(weibohot_data['data']))}条热搜、{'图片' if daily_image else '无图片'}")

    print("\n正在发送到pushplus...")
    message_payload = {
        "token": API_KEYS['pushplus_token'],
        "title": "伊蕾娜的每日播报",
        "content": final_content,
        "channel": "mail"
    }

    if DEBUG:
        print(f"pushplus请求payload: {json.dumps(message_payload, ensure_ascii=False)[:500]}...")

    message_response = requests.post(message_url, json=message_payload)
    print(f"pushplus接口状态码: {message_response.status_code}")
    print(f"pushplus响应: {message_response.text}")

    if message_response.headers.get('content-type') == 'application/json':
        push_result = message_response.json()
        print(f"pushplus响应解析成功，包含字段: {list(push_result.keys())}")
        if push_result.get("code") == 200:
            print("\n任务完成！")
            push_data['status'] = 'success'
            
            # 保存数据到数据库
            try:
                save_to_database(push_data)
                print("\n数据已成功保存到数据库！")
            except Exception as db_error:
                print(f"\n数据库保存失败: {db_error}")
                
            # 计算总执行时间
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            print(f"\n===== 程序执行完毕: {end_time.strftime('%Y-%m-%d %H:%M:%S')} =====")
            print(f"总执行时间: {total_time.total_seconds():.2f} 秒")
        else:
            print(f"\npushplus发送失败: {push_result.get('msg', '未知错误')}")
            push_data['status'] = 'failed'
            try:
                save_to_database(push_data)
                print("\n失败状态已保存到数据库！")
            except Exception as db_error:
                print(f"\n数据库保存失败: {db_error}")
            raise Exception(f"pushplus发送失败: {push_result.get('msg', '未知错误')}")
    else:
        print("\npushplus响应格式异常")
        push_data['status'] = 'failed'
        try:
            save_to_database(push_data)
            print("\n失败状态已保存到数据库！")
        except Exception as db_error:
            print(f"\n数据库保存失败: {db_error}")
        raise Exception("pushplus响应格式异常")

except requests.exceptions.RequestException as e:
    print(f"\n网络请求异常: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"  错误响应状态码: {e.response.status_code}")
        print(f"  错误响应内容: {e.response.text[:500]}...")
    # 保存失败状态到数据库
    if 'push_data' in locals():
        push_data['status'] = 'failed'
        try:
            save_to_database(push_data)
            print("\n失败状态已保存到数据库！")
        except Exception as db_error:
            print(f"\n数据库保存失败: {db_error}")
except json.JSONDecodeError as e:
    print(f"\nJSON解析错误: {e}")
    if 'push_data' in locals():
        push_data['status'] = 'failed'
        try:
            save_to_database(push_data)
            print("\n失败状态已保存到数据库！")
        except Exception as db_error:
            print(f"\n数据库保存失败: {db_error}")
except KeyError as e:
    print(f"\n数据结构错误，缺少必要字段: {e}")
    if 'push_data' in locals():
        push_data['status'] = 'failed'
        try:
            save_to_database(push_data)
            print("\n失败状态已保存到数据库！")
        except Exception as db_error:
            print(f"\n数据库保存失败: {db_error}")
except Exception as e:
    print(f"\n发生错误: {e}")
    import traceback

    print("\n详细错误堆栈:")
    traceback.print_exc()
    if 'push_data' in locals():
        push_data['status'] = 'failed'
        try:
            save_to_database(push_data)
            print("\n失败状态已保存到数据库！")
        except Exception as db_error:
            print(f"\n数据库保存失败: {db_error}")
finally:
    # 记录结束时间
    end_time = datetime.datetime.now()
    total_time = end_time - start_time
    print(f"\n===== 程序执行结束: {end_time.strftime('%Y-%m-%d %H:%M:%S')} =====")
    print(f"总执行时间: {total_time.total_seconds():.2f} 秒")
