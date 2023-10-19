import os
from datetime import datetime
import yaml
import logging
from monitor.validator import TimeValidation, CallMeLaterValidation
from config.setting import MONITOR_OBJECTS_DATA_SOURCE, MONITOR_OBJECTS_DATA_YAML_PATH
from notifier.wechat_template_message import WeChatTemplateMessage

logger = logging.getLogger(__name__)


class BaseMonitor(object):

    def __init__(self):
        self.send_group = None
        self.monitor_targets = self.get_monitor_targets()
        # self.notification_recipient_group = self.get_notification_recipient_group()
        self.Validations = [TimeValidation, CallMeLaterValidation]
        self.message_sender = [WeChatTemplateMessage]

    # def get_monitor_objects_data(self):
    #     """从配置文件或者数据库中获取监控对象的数据"""
    #     if MONITOR_OBJECTS_DATA_SOURCE == "yaml":
    #         project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         config_dir = os.path.join(project_path, MONITOR_OBJECTS_DATA_YAML_PATH)
    #         with open(config_dir, "r", encoding='utf-8') as f:
    #             return yaml.load(f, Loader=yaml.FullLoader)
    #     else:
    #         raise NotImplementedError

    # def get_notification_recipient_group(self):
    #     """从配置文件或者数据库中获取通知整个接收人组的数据"""
    #     if MONITOR_OBJECTS_DATA_SOURCE == "yaml":
    #         project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         config_dir = os.path.join(project_path, "datasource/notification_recipient_group.yaml")
    #         with open(config_dir, "r", encoding='utf-8') as f:
    #             return yaml.load(f, Loader=yaml.FullLoader)
    #     else:
    #         raise NotImplementedError

    def get_notify_recipient(self, msg) -> list:
        """提取对应组名对应的通知接收人信息"""

        raise NotImplementedError

    def get_monitor_targets(self) -> list:
        """获取监控对象"""
        raise NotImplementedError

    def perform_check(self):
        """监控"""
        raise NotImplementedError

    def send_notice(self):
        """发送通知"""
        raise NotImplementedError

    def validate(self, msg):
        """逐个验证"""
        for validation in self.Validations:
            msg = validation().validate(msg)
        return msg

    def generate_fault_ticket(self, msg: dict):
        """生成维护工单"""
        raise NotImplementedError

    def send_fault_notify(self, msg: dict):
        """发送故障通知"""
        try:
            msg = self.validate(msg)
        except Exception as e:
            logger.warning(f"验证失败:{e},取消发送")
            return
        # notify_group = msg.get('notify_group')
        recipients = self.get_notify_recipient(msg)
        if not recipients:
            logger.warning(f"没有找到对应的通知接收人,取消发送")
            return

        for sender in self.message_sender:
            # 为msg添加故障时间为当时的时间
            if not msg.get("fault_time"):
                msg["fault_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                msg["fault_time"] = msg.get("fault_time").strftime("%Y-%m-%d %H:%M:%S")

            for recipient in recipients:
                if recipient.get(sender.name.lower()):
                    msg["username"] = recipient.get("name")
                    msg['render_url'] = self.generate_fault_url(msg)
                    sender().send_fault_notify(user_info=recipient, message=msg)

    def generate_fault_url(self, msg: dict):
        """生成故障url"""
        return "www.baidu.com"

    def remove_fault_ticket_and_send_recover_notify(self, msg: dict):
        """故障清除"""
        raise NotImplementedError

    def is_fault_ticket_exist(self, msg: dict):
        """判断工单是否存在"""
        raise NotImplementedError

    def identify_message_and_send_notice(self, msg):
        """消息识别,并决定到底是否生成工单,发送什么类型的通知
        判定msg[is_online]是否为False
        is_online如果为False,
            则判断判断是否已经存在工单
                如果存在,则无需新建工单
                如果不存在,则新建工单
                执行validate后,发送notice
        is_online如果为True,
            则判断是否存在工单
                如果存在,则清除工单
                如果不存在,pass
        """
        if not msg['is_online']:
            if not self.is_fault_ticket_exist(msg):
                self.generate_fault_ticket(msg)
            self.send_fault_notify(msg)
        else:
            if self.is_fault_ticket_exist(msg):
                self.remove_fault_ticket_and_send_recover_notify(msg)
            else:
                pass

    def run(self):
        check_results = self.perform_check()
        for msg in check_results:
            self.identify_message_and_send_notice(msg)
