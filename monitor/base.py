from model.models import Group
from model.session import SessionLocal
from vaildator.validator import TimeValidation, UserNotifyFrequencyValidation, MessageReadValidation
from notifier.wechat_template_message import WeChatTemplateMessage
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class BaseMonitor(object):

    def __init__(self):
        self.send_group = None
        self.FAULTVALIDATORS = [TimeValidation, MessageReadValidation, UserNotifyFrequencyValidation, ]
        self.message_sender = [WeChatTemplateMessage]
        self.sql_session = None

    def __enter__(self):
        self.sql_session = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sql_session.close()
        # 如果数据库异常,则不会提交事务
        pass

    def get_notify_recipient(self, group_id: int) -> list:
        """
        提取对应组名对应的通知接收人信息
        :param group_id:
        :return: group_id对应的通知接收人列表,包含通知人的配置以{<notify_method>: <user_value>}形式
        """
        ret = []
        group = self.sql_session.query(Group).filter(Group.id == group_id).first()
        user_object_list = group.users
        for user_object in user_object_list:
            user_notify_config_list = user_object.notify_config
            user_info = {
                "user_id": user_object.id,
                "name": user_object.name,
                "gender": user_object.gender
            }
            for config in user_notify_config_list:
                if config.is_enable:
                    user_info[config.notify_method.lower()] = config.user_value
            ret.append(user_info)
        if not ret:
            logger.warning("没有找到组对应的通知接收人")
            raise ValueError("没有找到组对应的通知接收人")
        return ret

    def get_monitor_targets(self) -> list:
        """
        获取监控对象
        :return: 监控对象列表
        """
        raise NotImplementedError

    def perform_check(self) -> list:
        """
        执行检查
        :return: 返回检查结果的列表
        """
        raise NotImplementedError

    def send_notice(self, *args, **kwargs):
        """发送通知"""
        raise NotImplementedError

    @staticmethod
    def perform_validation(msg: dict, validations: list = None) -> dict:
        """
        验证消息
        :param validations: 验证器类列表
        :param msg: <dict>,单条的检查结果
        :return:
        """
        if not validations:
            return msg
        for validation in validations:
            msg = validation().validate(msg)
        return msg

    def analyze_message_and_send_notify(self, msg: dict) -> None:
        """分析消息并发送通知"""
        raise NotImplementedError

    def run(self):
        check_results = self.perform_check()
        if not check_results:
            logger.info("没有检测到异常")
            return
        for msg in check_results:
            self.analyze_message_and_send_notify(msg)
