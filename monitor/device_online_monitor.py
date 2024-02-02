import sqlalchemy
from datetime import datetime
from config.setting import NETLOC
from monitor.base import BaseMonitor
from vaildator.validator import BaseValidateError, TimeValidateError
from checker.devices_checker.checker import perform_async_check_devices
from config.message_template import DEVICE_FAULT_MESSAGE_TEMPLATE, DEVICE_RECOVER_MESSAGE_TEMPLATE
from model.models import Devices, FailureTicket
from urllib.parse import urlunparse, urlencode
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


# import logging
# logger = logging.getLogger(__name__)
# TODO:
# 1. 增加一个故障恢复按钮: 至恢复期不再发生故障通知,但是仍然会发送恢复通知

class DevicesOnlineMonitor(BaseMonitor):
    """设备监控"""

    def __init__(self):
        # self.sql_session = SessionLocal()
        self.fault_message_template = DEVICE_FAULT_MESSAGE_TEMPLATE
        self.recover_message_template = DEVICE_RECOVER_MESSAGE_TEMPLATE
        super().__init__()

    @staticmethod
    def convert_to_dict(obj):
        if obj is None:
            return None
        return {c.key: getattr(obj, c.key) for c in sqlalchemy.inspect(obj).mapper.column_attrs}

    def get_monitor_targets(self):
        """获取监控对象"""
        # sql_session = SessionLocal()
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
            # "group": device.group,
        } for device in devices]
        return devices_list
        # return self.get_monitor_objects_data()['devices']

    def perform_check(self):
        """执行设备检测"""
        targets = self.get_monitor_targets()
        return perform_async_check_devices(targets)

    def send_fault_notify(self, msg: dict):
        """发送故障通知"""
        group_id = msg.get("group_id")
        recipients = self.get_notify_recipient(group_id)
        if not recipients:
            logger.warning(f"没有找到对应的通知接收人,取消发送")
            return
        # 消息发送器发送消息
        for sender in self.message_sender:
            # 为msg添加故障时间为当时的时间
            if not msg.get("fault_time"):
                msg["fault_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                # 如果msg中已经有fault_time,则将其转换为字符串,原本为datetime对象
                msg["fault_time"] = msg.get("fault_time").strftime("%Y-%m-%d %H:%M:%S")

            for recipient in recipients:
                # recipient的格式为:
                # {   "user_id": 1,
                #     "name": "张三",
                #     <消息发送器的name>: <uuid>}
                if recipient.get(sender.name.lower()):
                    msg["recipient"] = recipient
                    msg['render_url'] = self.generate_fault_url(msg)
                    try:
                        msg = self.validate(msg)
                    except BaseValidateError as e:
                        logger.warning(f"验证失败:{e},取消发送")
                        return
                    sender().send_fault_notify(message=msg)

    def send_recover_notify(self, msg: dict) -> None:
        """发送恢复通知"""
        group_id = msg.get("group_id")
        recipients = self.get_notify_recipient(group_id)
        if not recipients:
            logger.warning(f"没有找到对应的通知接收人,取消发送")
            return
        # 消息发送器发送消息
        for sender in self.message_sender:
            # 为msg添加故障时间为当时的时间
            if not msg.get("recovery_time"):
                msg["recovery_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                # 如果msg中已经有recovery_time,则将其转换为字符串,原本为datetime对象
                msg["recovery_time"] = msg.get("recovery_time").strftime("%Y-%m-%d %H:%M:%S")

            for recipient in recipients:
                # recipient的格式为:
                # {   "user_id": 1,
                #     "name": "张三",
                #     <消息发送器的name>: <uuid>}
                if recipient.get(sender.name.lower()):
                    msg["recipient"] = recipient
                    msg['render_url'] = self.generate_recovery_url(msg)
                    try:
                        msg = self.validate(msg)
                    except BaseValidateError as e:
                        if not isinstance(e, TimeValidateError):
                            logger.info(f"验证不通过:{e},取消发送")
                            return
                        # logger.warning(f"验证失败:{e},取消发送")
                        # return
                    sender().send_recovery_notify(message=msg)

    def query_fault_ticket(self, msg: dict) -> list:
        """判断工单是否存在"""
        # logger.info(f"查询故障工单:{msg}")
        ret = []
        device_id = msg.get("id")
        devices = self.sql_session.query(FailureTicket).filter((FailureTicket.device_id == device_id) &
                                                               (FailureTicket.is_done != True)).all()
        if devices:
            msg["fault_ticket_id"] = devices[0].id
            ret = devices
        return ret

    def generate_fault_ticket(self, msg: dict):
        """生成维护工单,返回工单id"""
        device_id = msg.get("id")
        fault_ticket = FailureTicket(device_id=device_id, fault_time=msg['fault_time'], is_accepted=False,
                                     is_done=False)
        self.sql_session.add(fault_ticket)
        self.sql_session.commit()
        msg["fault_ticket_id"] = fault_ticket.id

    @staticmethod
    def generate_recovery_url():
        """生成恢复url"""
        return "www.baidu.com"

    def remove_fault_ticket(self, msg: dict, fault_tickets: list):
        """故障清除"""
        id_list = list(map(lambda x: x.id, fault_tickets))
        self.sql_session.query(FailureTicket).filter(FailureTicket.id.in_(id_list)).update(
            {"is_done": True, "recovery_time": msg["recovery_time"]})
        self.sql_session.commit()

    @staticmethod
    def generate_fault_url(msg: dict):
        """生成故障url"""

        scheme = 'http'
        netloc = NETLOC
        path = '/device_failure'
        query = {'ticket_id': msg['fault_ticket_id'], 'user_id': msg['recipient']['user_id']}
        query_string = urlencode(query)
        url = urlunparse((scheme, netloc, path, '', query_string, ""))
        logger.info(f"fault url:{url}")
        return url

    def analyze_message_and_send_notify(self, msg):
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
        # logger.info("begin identify message")
        if not msg['is_online']:
            # logger.info(f"发现故障:{msg}")
            # fault_tickets = self.query_fault_ticket(msg)
            # print(fault_tickets, "fault_tickets")
            if not self.query_fault_ticket(msg):
                # logger.info(f"没有发现故障工单,新建工单")
                self.generate_fault_ticket(msg)
                # logger.info(f"新建工单成功")
            self.send_fault_notify(msg)
            # logger.info(f"发送故障通知成功")
        else:
            # logger.info(f"设备在线:{msg}")
            fault_tickets = self.query_fault_ticket(msg)
            # logger.info(f"查询工单成功,工单编号:{fault_tickets}")
            if fault_tickets:
                # logger.info(f"有工单,发送恢复消息")
                msg["recovery_time"] = datetime.now()
                msg["fault_time"] = fault_tickets[0].fault_time.strftime("%Y-%m-%d %H:%M:%S")
                self.send_recover_notify(msg)
                self.remove_fault_ticket(msg, fault_tickets)
            else:
                pass
