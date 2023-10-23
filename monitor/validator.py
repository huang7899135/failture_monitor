from datetime import datetime
from config.setting import NOTICE_START_TIME, NOTICE_END_TIME
from abc import ABC, abstractmethod
from model.session import SessionLocal
from model.models import UserNotifyFrequency, FailureTicket
from sqlalchemy.orm import joinedload



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
    # FIXME: 未完成
    def validate(self, message):

        user_id = message.get("recipient").get("user_id")
        failure_ticket_id = message.get("fault_ticket_id")
        if not user_id and not failure_ticket_id:
            return message
        sql_session = SessionLocal()
        user_notify_frequency = (sql_session.query(UserNotifyFrequency)
                                 .join(FailureTicket,
                                       UserNotifyFrequency.failure_ticket_id == FailureTicket.id)  # 连接查询
                                 .filter(UserNotifyFrequency.user_id == user_id,
                                         UserNotifyFrequency.failure_ticket_id == failure_ticket_id,
                                         FailureTicket.is_done == False)
                                 .first())
        if user_notify_frequency:
            next_notify_time = user_notify_frequency.next_notify_time
            current_time = datetime.now()
            if next_notify_time > current_time:
                raise TimeValidateError("稍后回复")
        return message
