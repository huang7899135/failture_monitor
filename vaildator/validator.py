from datetime import datetime, timedelta
from config.setting import NOTICE_START_TIME, NOTICE_END_TIME
from abc import ABC, abstractmethod
from model.session import SessionLocal, get_session
from model.models import UserNotifyFrequency, FailureTicket
from celery.utils.log import get_task_logger
from config.setting import DEVICE_ONLINE_MONITOR_INTERVAL

logger = get_task_logger(__name__)
# logger = logging.getLogger(__name__)


class BaseValidateError(Exception):
    pass


class TimeValidateError(BaseValidateError):
    pass


class UserNotifyFrequencyValidateError(BaseValidateError):
    pass


class BaseValidation(ABC):
    """验证基类"""

    @abstractmethod
    def validate(self, message):
        raise NotImplementedError


class TimeValidation(BaseValidation):
    """时间限制"""

    def validate(self, message):
        current_time = datetime.now().time()
        fault_time_str = message.get("fault_time")
        datetime_object = datetime.strptime(fault_time_str, '%Y-%m-%d %H:%M:%S')
        # 从 datetime 对象获取 time 对象
        fault_time = datetime_object.time()
        # 保证不在通知时间内能至少发送一次通知
        if fault_time and (NOTICE_START_TIME < fault_time < NOTICE_END_TIME):
            fault_time_plus_10 = (datetime.combine(datetime.today(), fault_time) + timedelta(minutes=10)).time()
            if current_time < fault_time_plus_10:
                return message

        if current_time < NOTICE_START_TIME or current_time > NOTICE_END_TIME:
            raise TimeValidateError("不在通知时间段内")

        return message


class UserNotifyFrequencyValidation(BaseValidation):
    """稍后回复限制"""
    def validate(self, message):
        if not hasattr(message, "get"):
            logger.error(f"message:{message} is not dict")
            return message
        user_id = message.get("recipient").get("user_id")
        failure_ticket_id = message.get("fault_ticket_id")
        # 如果user_id和failure_ticket_id都不存在,则直接返回message
        if not user_id and not failure_ticket_id:
            return message
        sql_session = SessionLocal()
        sql_session.expire_all()
        user_notify_frequency = (sql_session.query(UserNotifyFrequency)
                                 .join(FailureTicket,
                                       UserNotifyFrequency.failure_ticket_id == FailureTicket.id)  # 连接查询
                                 .filter(UserNotifyFrequency.user_id == user_id,
                                         UserNotifyFrequency.failure_ticket_id == failure_ticket_id)
                                 .first())
        if user_notify_frequency:
            next_notify_time = user_notify_frequency.next_notify_time
            current_time = datetime.now()
            logger.warning(f"sqlalchemy query next_notify_time:{next_notify_time},current_time:{current_time}")
            if next_notify_time > current_time:
                raise UserNotifyFrequencyValidateError("延迟发送")
        sql_session.close()
        return message


class MessageReadValidation(BaseValidation):
    """消息是否已读"""
    # 查询UserNotifyFrequency的message_is_read字段,如果为True,且当前时间不属于整点到整点+5分钟的时间段内,则抛出异常
    def validate(self, message):
        if not hasattr(message, "get"):
            logger.error(f"message:{message} is not dict")
            return message
        failure_ticket_id = message.get("fault_ticket_id")
        if not failure_ticket_id:
            return message
        sql_session = SessionLocal()
        sql_session.expire_all()
        user_notify_frequency = (sql_session.query(UserNotifyFrequency)
                                 .filter(UserNotifyFrequency.failure_ticket_id == failure_ticket_id)
                                 .first())
        if user_notify_frequency:
            message_is_read = user_notify_frequency.message_is_read
            current_time = datetime.now()
            if message_is_read and current_time.minute > (DEVICE_ONLINE_MONITOR_INTERVAL / 60 + 2):
                raise UserNotifyFrequencyValidateError("消息已读,下一个整点再发送")
        sql_session.close()
        return message
