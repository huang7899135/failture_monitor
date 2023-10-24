from datetime import datetime
from config.setting import NOTICE_START_TIME, NOTICE_END_TIME
from abc import ABC, abstractmethod
from model.session import SessionLocal
from model.models import UserNotifyFrequency, FailureTicket
import logging

logger = logging.getLogger(__name__)


class TimeValidateError(Exception):
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
        if current_time < NOTICE_START_TIME or current_time > NOTICE_END_TIME:
            raise TimeValidateError("不在通知时间段内")
        return message


class UserNotifyFrequencyValidation(BaseValidation):
    """稍后回复限制"""
    # FIXME: 再celery查询出的user_nofify_frequency跟最新的值不一致?
    def validate(self, message):

        user_id = message.get("recipient").get("user_id")
        failure_ticket_id = message.get("fault_ticket_id")
        if not user_id and not failure_ticket_id:
            return message
        sql_session = SessionLocal()
        sql_session.expire_all()
        user_notify_frequency = (sql_session.query(UserNotifyFrequency)
                                 .join(FailureTicket,
                                       UserNotifyFrequency.failure_ticket_id == FailureTicket.id)  # 连接查询
                                 .filter(UserNotifyFrequency.user_id == user_id,
                                         UserNotifyFrequency.failure_ticket_id == failure_ticket_id,
                                         FailureTicket.is_done == False)
                                 .first())
        logger.debug(f"user_notify_frequency:{user_notify_frequency}")
        if user_notify_frequency:
            next_notify_time = user_notify_frequency.next_notify_time
            current_time = datetime.now()
            logger.debug(f"next_notify_time:{next_notify_time},current_time:{current_time}")
            if next_notify_time > current_time:
                raise TimeValidateError("稍后回复")

        return message
