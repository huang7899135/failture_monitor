from monitor.base import BaseMonitor
from checker.devices_checker.checker import perform_async_check_devices
from config.message_template import DEVICE_FAULT_MESSAGE_TEMPLATE, DEVICE_RECOVER_MESSAGE_TEMPLATE
from model.models import Devices, FailureTicket
from model.session import SessionLocal
from sqlalchemy.orm import class_mapper, ColumnProperty
import json
from urllib.parse import urlunparse, urlencode
import logging
logger = logging.getLogger(__name__)

class DevicesMonitor(BaseMonitor):
    """设备监控"""

    def __init__(self):
        self.sql_session = SessionLocal()
        self.fault_message_template = DEVICE_FAULT_MESSAGE_TEMPLATE
        self.recover_message_template = DEVICE_RECOVER_MESSAGE_TEMPLATE
        super().__init__()

    def get_monitor_targets(self):
        """获取监控对象"""
        devices = self.sql_session.query(Devices).filter(Devices.is_enable == True).all()
        devices_list = [{
            "id": device.id,
            "name": device.name,
            "location": device.location,
            "is_enable": device.is_enable,
            "device_type": device.device_type,
            "address": device.address,
            "port": device.port,
            "check_method": device.check_method,
            "group_id": device.group_id,
            "group": device.group
        } for device in devices]
        return devices_list
        # return self.get_monitor_objects_data()['devices']

    def get_notify_recipient(self, msg) -> list:
        """提取对应组名对应的通知接收人信息"""
        ret = []
        group = msg.get("group")
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
        return ret

    def perform_check(self):
        """执行设备检测"""
        return perform_async_check_devices(self.monitor_targets)

    def query_fault_ticket(self, msg: dict) -> list:
        """判断工单是否存在"""
        device_id = msg.get("id")
        devices = self.sql_session.query(FailureTicket).filter((FailureTicket.device_id == device_id) &
                                                               (FailureTicket.is_done != True)).all()
        if devices:
            msg["fault_ticket_id"] = devices[0].id
            return devices
        return []

    def generate_fault_ticket(self, msg: dict):
        """生成维护工单,返回工单id"""
        device_id = msg.get("id")
        fault_ticket = FailureTicket(device_id=device_id, fault_time=msg['fault_time'], is_accepted=False,
                                     is_done=False)
        self.sql_session.add(fault_ticket)
        self.sql_session.commit()
        msg["fault_ticket_id"] = fault_ticket.id

    def remove_fault_ticket(self, msg: dict, fault_tickets: list):
        """故障清除"""
        for fault_ticket in fault_tickets:
            fault_ticket.is_done = True
            fault_ticket.recovery_time = msg["recovery_time"]
        self.sql_session.commit()

    def generate_fault_url(self, msg: dict):
        """生成故障url"""

        scheme = 'http'
        netloc = '192.168.68.179:8090'
        path = '/device_failure'
        query = {'ticket_id': msg['fault_ticket_id'], 'user_id': msg['recipient']['user_id']}
        query_string = urlencode(query)
        url = urlunparse((scheme, netloc, path, '', query_string, ""))
        logger.info(f"fault url:{url}")
        return url
