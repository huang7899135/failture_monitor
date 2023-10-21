from abc import ABC, abstractmethod


class Notifier(ABC):
    name = None

    @abstractmethod
    def send_fault_notify(self, message: dict):
        """发送故障通知"""
        raise NotImplementedError

    @abstractmethod
    def send_recovery_notify(self, message: dict):
        """发送网络恢复通知"""
        raise NotImplementedError
