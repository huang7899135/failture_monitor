from datetime import datetime
from config.setting import NOTICE_START_TIME, NOTICE_END_TIME
from abc import ABC, abstractmethod


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


class CallMeLaterValidation(BaseValidation):
    """稍后回复限制"""

    def validate(self, message):
        return message
