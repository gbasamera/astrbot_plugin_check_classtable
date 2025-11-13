from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.star.filter.event_message_type import EventMessageType
from astrbot.api import AstrBotConfig


import json
import os
from datetime import datetime
from typing import List, Dict, Set, Optional
from pathlib import Path

# 简化版自然语言时间解析器
def parse_natural_time(text: str) -> Dict:
    """简化版自然语言时间解析器"""
    result = {"weekday": 0, "sections": []}
    
    weekdays = {
        "周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6,
        "星期一": 0, "星期二": 1, "星期三": 2, "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6
    }
    
    for weekday_name, weekday_num in weekdays.items():
        if weekday_name in text:
            result["weekday"] = weekday_num
            break
    
    if "上午" in text or "早上" in text or "早" in text:
        result["sections"] = [1, 2, 3, 4]
    elif "下午" in text:
        result["sections"] = [5, 6, 7, 8]
    elif "晚上" in text or "晚" in text:
        result["sections"] = [9, 10, 11]
    elif "一二节" in text:
        result["sections"] = [1, 2]
    elif "三四节" in text:
        result["sections"] = [3, 4]
    elif "五六节" in text:
        result["sections"] = [5, 6]
    elif "七八节" in text:
        result["sections"] = [7, 8]
    else:
        result["sections"] = [1, 2, 3, 4]
    
    return result

class FreeMembersPlugin:
    def __init__(self, context: Context, config: AstrBotConfig):
        """
        初始化无课干事查询插件
        """
        self.conf = config

        self.data_file = self._find_or_create_data_file()
        self.schedule_data = self.conf["pathfile"]
        self.all_members = self.get_all_members()
    
    def _find_or_create_data_file(self, data_file: str | None = None) -> str:
        """查找或创建数据文件（改为在同级schedule文件夹中）"""
        # 定义schedule文件夹路径（同级目录）
        schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
        
        # 如果指定了文件路径，直接使用
        if data_file and os.path.exists(data_file):
            logger.info(f"使用指定文件: {data_file}")
            return data_file
        
        # 搜索可能的文件路径（优先schedule文件夹）
        possible_paths = [
            os.path.join(schedule_dir, "all_schedules.json"),
            os.path.join(schedule_dir, "schedule_data.json"),
            "all_schedules.json",
            "data/all_schedules.json",
            "../all_schedules.json",
            "./data/all_schedules.json",
            "schedule_data.json",
            "data/schedule_data.json"
        ]
        
        # 添加插件目录搜索
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.extend([
            os.path.join(plugin_dir, "all_schedules.json"),
            os.path.join(plugin_dir, "data/all_schedules.json"),
            os.path.join(plugin_dir, "../all_schedules.json")
        ])
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ 找到课表数据文件: {path}")
                return path
        
        # 如果都没找到，创建示例数据文件（在schedule文件夹中）
        logger.warning("❌ 未找到课表数据文件，创建示例文件...")
        return self._create_sample_data_file(schedule_dir)
    
    def _create_sample_data_file(self, schedule_dir: str) -> str:
        """创建示例数据文件（在schedule文件夹中）"""
        # 确保schedule文件夹存在
        if not os.path.exists(schedule_dir):
            try:
                os.makedirs(schedule_dir)
                logger.info(f"✅ 已创建schedule文件夹: {schedule_dir}")
            except Exception as e:
                logger.error(f"❌ 创建schedule文件夹失败: {e}")
                # 失败时退回到插件同级目录
                schedule_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 创建示例数据，符合 schedule_model.py 的结构
        sample_data = [
            {
                "name": "王闯",
                "semester": "2024-2025-1",
                "class_name": "计算机1班",
                "major": "计算机科学",
                "college": "计算机学院",
                "table": self._create_sample_schedule()
            },
            {
                "name": "王雅馨", 
                "semester": "2024-2025-1",
                "class_name": "计算机1班",
                "major": "计算机科学",
                "college": "计算机学院",
                "table": self._create_sample_schedule()
            },
            {
                "name": "杨彦萍",
                "semester": "2024-2025-1", 
                "class_name": "计算机1班",
                "major": "计算机科学",
                "college": "计算机学院",
                "table": self._create_sample_schedule()
            },
            {
                "name": "姜元皓",
                "semester": "2024-2025-1",
                "class_name": "计算机1班", 
                "major": "计算机科学",
                "college": "计算机学院",
                "table": self._create_sample_schedule()
            },
            {
                "name": "石浩霖",
                "semester": "2024-2025-1",
                "class_name": "计算机1班",
                "major": "计算机科学",
                "college": "计算机学院",
                "table": self._create_sample_schedule()
            }
        ]
        
        # 保存到schedule文件夹中的all_schedules.json
        file_path = os.path.join(schedule_dir, "all_schedules.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 已创建示例数据文件: {os.path.abspath(file_path)}")
            logger.info(f"📁 文件位置: {file_path}")
            logger.info(f"👥 示例干事: 王闯、王雅馨、杨彦萍、姜元皓、石浩霖")
            logger.info("💡 请用真实的课表数据替换此文件")
            
            return file_path
            
        except Exception as e:
            logger.error(f"❌ 创建示例文件失败: {e}")
            # 失败时退回到插件同级目录创建
            fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "all_schedules.json")
            return fallback_path
    
    def _create_sample_schedule(self):
        """创建示例课表数据结构（11节×7天×20周）"""
        # 创建空的课表（全部无课）
        schedule = [[[0 for _ in range(20)] for _ in range(7)] for _ in range(11)]
        
        # 添加一些示例课程（周一上午1-2节在第1-10周有课）
        for week in range(10):  # 第1-10周
            schedule[0][0][week] = 1  # 周一第1节
            schedule[1][0][week] = 1  # 周一第2节
        
        # 周三下午5-6节在第5-15周有课
        for week in range(4, 15):  # 第5-15周
            schedule[4][2][week] = 1  # 周三第5节
            schedule[5][2][week] = 1  # 周三第6节
            
        return schedule
    
    def load_schedule_data(self) -> List[Dict]:
        """加载课表数据"""
        try:
            if not os.path.exists(self.data_file):
                logger.error(f"❌ 课表数据文件不存在: {self.data_file}")
                # 尝试创建示例文件
                schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
                self.data_file = self._create_sample_data_file(schedule_dir)
                if not os.path.exists(self.data_file):
                    return []
            
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ 成功加载 {len(data)} 个干事的课表数据")
                logger.info(f"📁 数据文件: {os.path.abspath(self.data_file)}")
                
                # 显示干事名单
                names = [person.get('name', '未知') for person in data]
                logger.info(f"👥 干事名单: {', '.join(names)}")
                
                return data
                
        except Exception as e:
            logger.error(f"❌ 加载课表数据失败: {e}")
            return []
    
    def get_all_members(self) -> List[str]:
        """获取所有干事姓名列表"""
        if not self.schedule_data:
            return []
        
        members = []
        for person in self.schedule_data:
            name = person.get("name")
            if name is not None:
                members.append(str(name))
            else:
                members.append("未知")
        
        return members
    
    def get_current_week(self) -> int:
        """获取当前周次"""
        try:
            semester_start = datetime(2024, 9, 2)
            today = datetime.now()
            delta = today - semester_start
            current_week = delta.days // 7 + 1
            return max(1, min(20, current_week))
        except:
            return 1
    
    def is_member_free(self, name: str, weekday: int, periods: List[int], week: int = 0) -> bool:
        """判断干事在指定时间段是否无课"""
        if week == 0:
            week = self.get_current_week()
        
        if not name or not isinstance(name, str):
            return False
        
        person_data = None
        for person in self.schedule_data:
            if person.get("name") == name:
                person_data = person
                break
        
        if not person_data or "table" not in person_data:
            return False
        
        schedule = person_data["table"]
        
        for period in periods:
            weekday_idx = weekday - 1
            period_idx = period - 1
            week_idx = week - 1
            
            # 检查索引是否在有效范围内
            if (period_idx < 0 or period_idx >= len(schedule) or
                weekday_idx < 0 or weekday_idx >= len(schedule[period_idx]) or
                week_idx < 0 or week_idx >= len(schedule[period_idx][weekday_idx])):
                continue
            
            if schedule[period_idx][weekday_idx][week_idx] == 1:
                return False  # 有课
        
        return True
    
    def get_free_members_by_time(self, weekday: int, periods: List[int], week: int = 0) -> List[str]:
        """获取在指定时间段无课的所有干事"""
        if week == 0:
            week = self.get_current_week()
            
        free_members = []
        for name in self.all_members:
            if name and self.is_member_free(name, weekday, periods, week):
                free_members.append(name)
        return free_members
    
    def parse_time_range(self, time_description: str) -> Dict:
        """解析时间段描述"""
        if not time_description or not isinstance(time_description, str):
            return {"weekday": 1, "periods": [1, 2, 3, 4]}
        
        try:
            time_info = parse_natural_time(time_description)
        except Exception as e:
            logger.error(f"时间解析失败: {e}")
            time_info = {"weekday": 0, "sections": []}
        
        result = {
            "weekday": time_info.get("weekday", 0) + 1,
            "periods": time_info.get("sections", []),
        }
        
        if not result["periods"]:
            if "上午" in time_description or "早" in time_description:
                result["periods"] = [1, 2, 3, 4]
            elif "下午" in time_description:
                result["periods"] = [5, 6, 7, 8]
            elif "晚上" in time_description:
                result["periods"] = [9, 10, 11]
            else:
                result["periods"] = list(range(1, 9))
        
        return result
    
    def find_free_members(self, time_description: str, week: int = 0) -> Dict:
        """一键查找无课干事"""
        if week == 0:
            week = self.get_current_week()
            
        default_result = {
            "time_description": time_description or "未知时间",
            "weekday": 1, "weekday_str": "周一",
            "periods": [1, 2, 3, 4], "periods_str": "第1、2、3、4节",
            "week": week or 1, "free_members": [], "busy_members": [],
            "free_count": 0, "total_count": 0, "free_percentage": 0.0
        }
        
        if not self.schedule_data:
            default_result["error"] = "无课表数据"
            return default_result
        
        try:
            time_info = self.parse_time_range(time_description)
            weekday = time_info["weekday"]
            periods = time_info["periods"]
            
            free_members = self.get_free_members_by_time(weekday, periods, week)
            busy_members = [name for name in self.all_members if name not in free_members]
            
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            weekday_str = weekday_names[weekday-1] if 1 <= weekday <= 7 else f"周{weekday}"
            periods_str = "、".join([f"第{period}节" for period in periods])
            
            total_count = len(self.all_members)
            free_count = len(free_members)
            free_percentage = round(free_count / total_count * 100, 1) if total_count > 0 else 0
            
            return {
                "time_description": time_description,
                "weekday": weekday, "weekday_str": weekday_str,
                "periods": periods, "periods_str": periods_str,
                "week": week, "free_members": free_members,
                "busy_members": busy_members, "free_count": free_count,
                "total_count": total_count, "free_percentage": free_percentage
            }
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            default_result["error"] = f"查询失败: {str(e)}"
            return default_result
    
    def format_result(self, result: Dict) -> str:
        """格式化查询结果为可读字符串"""
        if "error" in result:
            return f"❌ {result.get('error', '未知错误')}"
        
        time_description = result.get("time_description", "未知时间")
        weekday_str = result.get("weekday_str", "未知星期")
        periods_str = result.get("periods_str", "未知节次")
        week = result.get("week", 1)
        total_count = result.get("total_count", 0)
        free_count = result.get("free_count", 0)
        free_percentage = result.get("free_percentage", 0.0)
        free_members = result.get("free_members", [])
        busy_members = result.get("busy_members", [])
        
        output = []
        output.append(f"📊 无课干事查询结果")
        output.append(f"⏰ 时间: {weekday_str} {periods_str} (第{week}周)")
        output.append(f"👥 总人数: {total_count}人")
        output.append(f"🆓 无课人数: {free_count}人 ({free_percentage}%)")
        output.append("")
        
        if free_members:
            output.append("✅ 无课干事:")
            free_list = "、".join(free_members)
            output.append(f"   {free_list}")
        else:
            output.append("❌ 该时间段无人无课")
        
        if busy_members:
            output.append("")
            output.append("📚 有课干事:")
            busy_list = "、".join(busy_members)
            output.append(f"   {busy_list}")
        
        return "\n".join(output)
    
    def quick_call_free_members(self, time_description: str, week: int = 0) -> str:
        """一键呼出无课干事"""
        if week == 0:
            week = self.get_current_week()
            
        if not time_description or not isinstance(time_description, str):
            time_description = "今天"
        
        if not self.schedule_data:
            schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
            file_path = os.path.join(schedule_dir, "all_schedules.json")
            return f"❌ 未找到课表数据\n💡 已自动创建示例文件，请用真实数据替换: {os.path.abspath(file_path)}"
        
        result = self.find_free_members(time_description, week)
        return self.format_result(result)


@register("check_classtable", "gbasamera", "识别课表，一键呼出无课干事", "1.0.0")
class CheckClassTable(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.plugin = FreeMembersPlugin(context, config = AstrBotConfig())    
    async def initialize(self):
        """插件初始化"""
        logger.info("✅ 课表查询插件已启动")
        
        if self.plugin.schedule_data:
            members = self.plugin.all_members
            logger.info(f"✅ 成功加载 {len(members)} 个干事的课表")
            logger.info(f"👥 干事名单: {', '.join(members)}")
            logger.info(f"📁 数据文件: {os.path.abspath(self.plugin.data_file)}")
        else:
            logger.warning("⚠️ 使用示例数据文件")
            schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
            file_path = os.path.join(schedule_dir, "all_schedules.json")
            logger.info(f"💡 请用真实的课表数据替换: {os.path.abspath(file_path)}")

    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def handle_message(self, event: AstrMessageEvent) -> MessageEventResult:
        """处理群消息"""
        try:
            message = event.message_str.strip()
            if not message:
                return MessageEventResult()
            
            logger.info(f"📨 收到消息: {message}")
            
            response = self.process_query(message)
            if response:
                # 在回复中添加文件位置信息（如果是示例数据）
                if not self.plugin.schedule_data or len(self.plugin.schedule_data) <= 5:  # 示例数据只有5个人
                    schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
                    file_path = os.path.join(schedule_dir, "all_schedules.json")
                    response += f"\n\n💡 当前使用示例数据，文件位置: {os.path.abspath(file_path)}"
                
                return event.plain_result(response)
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            return event.plain_result("❌ 查询失败，请稍后重试")
        
        return MessageEventResult()
    
    def process_query(self, message: str) -> str:
        """处理查询消息"""
        if not message or not isinstance(message, str):
            return ""
        
        # 文件状态查询
        if "文件" in message or "位置" in message or "路径" in message:
            return self.show_file_info()
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["帮助", "help", "怎么用"]):
            return self.show_help()
        
        if any(keyword in message_lower for keyword in ["统计", "状态"]):
            return self.schedule_stats()
        
        if any(keyword in message for keyword in ["无课", "没课", "空闲", "谁有空", "呼人"]):
            time_desc = self.extract_time_from_message(message)
            return self.quick_call(time_desc)
        
        time_keywords = ["今天", "明天", "后天", "周一", "周二", "周三", "周四", "周五", "周六", "周日", 
                        "上午", "下午", "晚上", "一二节", "三四节", "五六节", "七八节"]
        if any(keyword in message for keyword in time_keywords):
            return self.quick_call(message)
        
        return ""
    
    def show_file_info(self) -> str:
        """显示文件信息"""
        file_path = self.plugin.data_file
        abs_path = os.path.abspath(file_path)
        exists = os.path.exists(file_path)
        data_count = len(self.plugin.schedule_data)
        
        info = f"📁 数据文件信息:\n"
        info += f"📍 路径: {abs_path}\n"
        info += f"📊 状态: {'✅ 存在' if exists else '❌ 不存在'}\n"
        info += f"👥 数据: {data_count} 个干事\n"
        
        if data_count > 0:
            members = self.plugin.all_members[:5]  # 显示前5个
            info += f"📋 干事: {', '.join(members)}"
            if data_count > 5:
                info += f" 等{data_count}人"
        
        if data_count <= 5:  # 可能是示例数据
            schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
            file_path = os.path.join(schedule_dir, "all_schedules.json")
            info += f"\n\n💡 这是示例数据，请用真实课表数据替换此文件: {os.path.abspath(file_path)}"
        
        return info
    
    def extract_time_from_message(self, message: str) -> str:
        """从消息中提取时间描述"""
        if not message or not isinstance(message, str):
            return "今天"
        
        time_keywords = ["今天", "明天", "后天", "周一", "周二", "周三", "周四", "周五", "周六", "周日", 
                        "上午", "下午", "晚上", "一二节", "三四节", "五六节", "七八节"]
        
        for keyword in time_keywords:
            if keyword in message:
                return keyword
        
        now = datetime.now()
        current_weekday = now.weekday() + 1
        
        if current_weekday <= 5:
            current_hour = now.hour
            if 8 <= current_hour < 12:
                return "今天上午"
            elif 14 <= current_hour < 18:
                return "今天下午"
        
        return "今天"
    
    def quick_call(self, time_desc: str = "今天") -> str:
        """一键呼出无课干事"""
        if not time_desc or not isinstance(time_desc, str):
            time_desc = "今天"
        
        try:
            return self.plugin.quick_call_free_members(time_desc)
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return f"❌ 查询失败: {str(e)}"
    
    def schedule_stats(self) -> str:
        """课表统计信息"""
        if not self.plugin.schedule_data:
            schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
            file_path = os.path.join(schedule_dir, "all_schedules.json")
            return f"❌ 未找到课表数据\n💡 已自动创建示例文件，请用真实数据替换: {os.path.abspath(file_path)}"
        
        total = len(self.plugin.all_members)
        if total == 0:
            return "❌ 课表数据为空"
        
        output = [f"📊 课表统计 (共{total}人)"]
        
        try:
            time_slots = ["上午", "下午"]
            weekday_names = ["周一", "周二", "周三", "周四", "周五"]
            
            for slot in time_slots:
                free_counts = []
                for weekday in range(1, 6):
                    result = self.plugin.find_free_members(f"{weekday_names[weekday-1]}{slot}")
                    free_counts.append(result["free_count"])
                
                avg_free = sum(free_counts) / len(free_counts) if free_counts else 0
                avg_percentage = round(avg_free / total * 100, 1)
                output.append(f"{slot}: 平均{avg_free:.1f}人无课 ({avg_percentage}%)")
                
        except Exception as e:
            output.append(f"统计计算出错: {e}")
        
        return "\n".join(output)
    
    def show_help(self) -> str:
        """显示帮助信息"""
        schedule_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schedule")
        file_path = os.path.join(schedule_dir, "all_schedules.json")
        help_text = f"""
📋 课表查询插件使用说明

🔍 查询命令：
• "周二上午无课" - 查询周二上午无课干事
• "谁周三下午有空" - 查询周三下午空闲人员
• "一键呼人" - 自动查询当前时间段
• "课表统计" - 查看整体统计信息
• "文件位置" - 查看数据文件信息

⏰ 支持的时间格式：
• 今天/明天/后天 + 上午/下午/晚上
• 周一至周日 + 时间段
• 具体节次：一二节、三四节等

💡 示例：
• "周二上午谁没课"
• "明天下午呼人" 
• "周三三四节空闲查询"
• "文件在哪里"

📝 注意：请用真实课表数据替换以下文件
📍 {os.path.abspath(file_path)}
        """
        return help_text.strip()

    async def terminate(self):
        """插件卸载"""
        logger.info("课表查询插件已卸载")
