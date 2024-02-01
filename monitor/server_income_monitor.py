import calendar
from model.session import SessionLocal
from monitor.base import BaseMonitor
from model.models import IncomeMonitorPlatform, IncomeMonitorServer
import importlib
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta

logger = get_task_logger(__name__)


class ServerIncomeMonitor(BaseMonitor):

    def __init__(self):
        super().__init__()
        self.sql_session = None

    def __enter__(self):
        self.sql_session = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sql_session.close()
        pass

    def get_monitor_targets(self) -> list:
        return []

    def get_monitor_target_class(self) -> list:
        """
        遍历IncomeMonitorPlatform,找出寻找同名的platform类
        :return:webpage_checker.sites下的需要监控的类
        """
        monitor_platform_list = self.sql_session.query(IncomeMonitorPlatform).filter(
            IncomeMonitorPlatform.is_enable == True).all()
        if not monitor_platform_list:
            return []
        monitor_platform_class_list = []
        for monitor_platform in monitor_platform_list:
            class_name = monitor_platform.platform
            base_path = "checker.webpage_checker.sites"
            module_path = f"{base_path}.{class_name.lower()}"
            # 动态导入模块
            module = importlib.import_module(module_path)
            # 获取类
            monitor_platform_class_list.append(getattr(module, class_name))
        return monitor_platform_class_list

    def perform_check(self):
        """监控"""
        ret = []
        monitor_class = self.get_monitor_target_class()
        for monitor in monitor_class:
            with monitor() as m:
                problem_servers = m.perform_income_check().get("problem_servers")
                if problem_servers:
                    ret.extend(problem_servers)
        return ret

    def send_notice(self, msg: dict):
        """发送通知"""
        group_id = msg.get("group_id")
        recipients = self.get_notify_recipient(group_id)
        if not recipients:
            logger.warning(f"没有找到对应的通知接收人,取消发送")
            return
        # 消息发送器发送消息
        for sender in self.message_sender:
            for recipient in recipients:
                # recipient的格式为:
                # {   "user_id": 1,
                #     "name": "张三",
                #     <消息发送器的name>: <uuid>}
                user_value = recipient.get(sender.name.lower())
                if user_value:
                    # TODO:微信模板消息服务器收入异常
                    sender().send_abnormal_equipment_notification(
                        to_user=user_value,
                        render_url=msg.get('render_url', "www.baidu.com"),
                        equipment_type=msg.get("equipment_type", "服务器"),
                        equipment_name=msg.get("device_sn", "未知"),
                        fault_date=msg.get("fault_time", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")),
                        fault_location=msg.get("location", "未知"),
                        fault_reason=msg.get("description", "未知")
                    )
                    # sender().send_network_anomaly_notification(message=msg)

    def analyze_message_and_send_notify(self, msg: dict) -> None:
        """
        分析perform_check返回的结果并发送通知
        :param msg: perform_check返回的结果的单条
        :return:
        """
        self.send_notice(msg)
