# -*- coding: utf-8 -*-
"""
natural_time_parser.py
-----------------------------------
自然语言时间解析模块

功能：
- 将诸如 “明天下午三点”、“后天第七八节”、“星期五晚上六点半” 等中文口语化时间
  转换为结构化的标准时间表示。
- 返回统一格式：
    {
        "date": datetime.date,          # 日期
        "weekday": int,                 # 周几（0=周一）
        "sections": [5,6,7],            # 节次（若为节次表达）
        "time_range": ((h1, m1), (h2, m2))  # 时间段（若为时刻表达）
    }

用途：
- 结合课程表数据，判断学生在某时间是否有课、何时空闲等。

"""

from datetime import datetime, timedelta
import re


# ============================================
# 一、中文数字转数字
# ============================================
def chinese_to_digit(s: str) -> int:
    """
    将中文数字（如“三点半”、“十”、“十一”）转换为阿拉伯数字
    """
    table = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if s.isdigit():
        return int(s)
    total = 0
    if len(s) == 1:
        return table.get(s, 0)
    if s[0] == "十":  # 十一、十二……
        return 10 + table.get(s[1], 0)
    if s[-1] == "十":  # 二十、三十
        return table.get(s[0], 0) * 10
    if "十" in s:
        parts = s.split("十")
        return table.get(parts[0], 0) * 10 + table.get(parts[1], 0)
    return 0


# ============================================
# 二、节次映射表
# ============================================
SECTION_TIME_MAP = {
    # 节次 : (开始时间, 结束时间)
    (1, 2): ((8, 0), (10, 0)),
    (3, 4): ((10, 0), (12, 0)),
    (5, 6): ((14, 30), (16, 30)),
    (7, 8): ((16, 30), (18, 20)),
    (9, 11): ((19, 0), (21, 50)),
}

# 用于快速查找“第七八节” → [7,8]
SECTION_NAME_MAP = {
    "一二节": [1, 2],
    "三四节": [3, 4],
    "五六节": [5, 6],
    "七八节": [7, 8],
    "九十节": [9, 10],
    "十一节": [11],
}

# ============================================
# 三、时间段映射表
# ============================================
TIME_PHRASE_MAP = {
    "早上": ((8, 0), (12, 0)),
    "上午": ((8, 0), (12, 0)),
    "中午": ((12, 0), (14, 0)),
    "下午": ((14, 0), (17, 30)),
    "晚上": ((17, 0), (22, 0))
}

# ============================================
# 四、星期映射表
# ============================================
WEEKDAY_MAP = {
    "一": 0, 
    "二": 1, 
    "三": 2, 
    "四": 3, 
    "五": 4, 
    "六": 5, 
    "日": 6, 
    "天": 6
    }


# ============================================
# 五、核心解析函数
# ============================================
def parse_natural_time(text: str, base_date: datetime):
    """
    将中文自然语言时间短语解析为结构化时间信息
    """
    if base_date is None:
        base_date = datetime.now()

    text = text.strip()
    result = {
        "date": None,
        "weekday": None,
        "sections": [],
        "time_range": None
    }

    # --------------------
    # 1️⃣ 日期偏移解析
    # --------------------
    day_offset = 0
    if "前天" in text:
        day_offset = -2
    elif "昨天" in text:
        day_offset = -1
    elif "今天" in text:
        day_offset = 0
    elif "明天" in text:
        day_offset = 1
    elif "后天" in text:
        day_offset = 2

    date = base_date + timedelta(days=day_offset)

    # --------------------
    # 2️⃣ 星期解析
    # --------------------
    week_match = re.search(r"([上下本]?周)([一二三四五六日天])", text)
    if week_match:
        prefix, day_ch = week_match.groups()
        weekday = WEEKDAY_MAP[day_ch]
        base_weekday = base_date.weekday()
        week_offset = 0
        if "下" in prefix:
            week_offset = 1
        elif "上" in prefix:
            week_offset = -1
        delta_days = (weekday - base_weekday) % 7 + week_offset * 7
        date = base_date + timedelta(days=delta_days)
        result["weekday"] = weekday
    else:
        result["weekday"] = date.weekday()

    result["date"] = date.date()

    # --------------------
    # 3️⃣ 节次解析
    # --------------------
    for name, sections in SECTION_NAME_MAP.items():
        if name in text:
            result["sections"] = sections
            # 找节次对应时间
            for (key, timepair) in SECTION_TIME_MAP.items():
                if set(sections).issubset(set(range(key[0], key[1] + 1))):
                    result["time_range"] = timepair
                    break
            break

    # --------------------
    # 4️⃣ 时间段关键字解析
    # --------------------
    for phrase, timepair in TIME_PHRASE_MAP.items():
        if phrase in text:
            result["time_range"] = timepair
            break

    # --------------------
    # 5️⃣ 具体几点几分解析
    # --------------------
    match = re.search(r"([早上上午中午下午傍晚晚上]?)([一二三四五六七八九十\d]+)点(半)?", text)
    if match:
        period, hour_str, half = match.groups()
        hour = chinese_to_digit(hour_str)
        if period in ("下午", "晚上") and hour < 12:
            hour += 12
        minute = 30 if half else 0
        result["time_range"] = ((hour, minute), (hour, minute))

    return result


# ============================================
# 六、测试代码（独立运行时使用）
# ============================================
if __name__ == "__main__":
    examples = [
        "明天下午三点",
        "后天第七八节",
        "星期五晚上六点半",
        "今天上午",
        "下周一下午五六节",
        "后天晚上",
    ]
    for e in examples:
        print(f"{e} → {parse_natural_time(e, datetime.now())}\n")