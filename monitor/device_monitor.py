from monitor.base import BaseMonitor
from checker.devices_checker.checker import perform_async_check_devices
from config.message_template import DEVICE_FAULT_MESSAGE_TEMPLATE, DEVICE_RECOVER_MESSAGE_TEMPLATE
from model.models import Devices, Failure_ticket
from model.session import SessionLocal
from sqlalchemy.orm import class_mapper, ColumnProperty
import json


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

    def is_fault_ticket_exist(self, msg: dict):
        """判断工单是否存在"""
        device_id = msg.get("id")
        devices = self.sql_session.query(Failure_ticket).filter(Failure_ticket.device_id == device_id
                                                                and Failure_ticket.is_done != True).all()
        if devices:
            return True
        return False

    def generate_fault_ticket(self, msg: dict):
        """生成维护工单"""
        device_id = msg.get("id")
        device = self.sql_session.query(Devices).filter(Devices.id == device_id).first()
        fault_ticket = Failure_ticket(device_id=device_id, fault_time=msg['fault_time'], is_accepted=False,
                                      is_done=False)
        self.sql_session.add(fault_ticket)
        self.sql_session.commit()

    def object_as_dict(self, obj):
        """Converts an SQLAlchemy object to a dictionary."""
        # return {column.key: getattr(obj, column.key)
        #         for column in class_mapper(obj.__class__).mapped_table.c}

        data = {}
        for prop in class_mapper(obj.__class__).iterate_properties:
            if isinstance(prop, ColumnProperty):
                data[prop.key] = getattr(obj, prop.key)
            else:
                # Handle relationships (e.g., ForeignKey)
                rel = getattr(obj, prop.key)
                if rel is not None:
                    if isinstance(rel, list):  # For one-to-many or many-to-many relationships
                        data[prop.key] = [self.object_as_dict(item) for item in rel]
                    else:  # For one-to-one or many-to-one relationships
                        data[prop.key] = self.object_as_dict(rel)
        return data
