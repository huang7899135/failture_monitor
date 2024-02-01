import time
import requests
import json
from config import wechat_secret
import pickle
import logging
import os

from config.message_template import DEVICE_FAULT_MESSAGE_TEMPLATE, DEVICE_RECOVER_MESSAGE_TEMPLATE
from notifier.BaseNotifier import Notifier
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


# logger = logging.getLogger(__name__)


class WeChatTemplateMessage(Notifier):
    name = "wechatTemplateMessage"
    token = None
    token_expiry_time = 0
    token_path = os.path.join(os.path.dirname(__file__), 'token/wechat_token')
    app_id = wechat_secret.APPID  # 开发者ID
    app_secret = wechat_secret.APP_SECRET  # 开发者密匙，妥善保管

    def __init__(self):

        self.load_token()
        self.max_retry = 3

    @classmethod
    def load_token(cls):
        """加载本地token,如果本地没有token文件,则初始化token为None"""
        if os.path.exists(cls.token_path):
            with open(cls.token_path, 'rb') as f:
                try:
                    ret = pickle.load(f)
                    logger.info(f"本地token加载成功")
                    cls.token = ret.get('token')
                    cls.token_expiry_time = ret.get('expiry_time')
                    return None
                except Exception as e:
                    logger.warning(f"token加载出错:{e}")
        logger.debug(f"本地暂无token文件")
        cls.token = None
        cls.token_expiry_time = 0

    @classmethod
    def save_token(cls):
        data = {'token': cls.token, 'expiry_time': cls.token_expiry_time}
        try:
            with open(cls.token_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"token保存失败:{e}")
        logger.debug("token保存成功")

    @classmethod
    def get_token(cls):
        """获取access_token"""
        current_time = int(time.time())
        if cls.token is None or current_time >= cls.token_expiry_time:
            logger.debug("token过期,从新获取token")
            cls.get_token_from_server()
        return cls.token

    @classmethod
    def get_token_from_server(cls):
        """从新请求token"""
        current_time = int(time.time())
        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=" + cls.app_id + "&secret=" + cls.app_secret
        res = requests.get(url).json()
        if "access_token" in res:
            logger.debug("获取到token")
            cls.token = res["access_token"]
            cls.token_expiry_time = current_time + res["expires_in"]
            cls.save_token()
        else:
            logger.critical("获取token失败")
            # cls.token = None
            # cls.token_expiry_time = 0
            raise Exception(f"获取token失败,{res['errmsg']}")

    def __send_messages(self, to_user, template_id, render_url, template_data):
        """
        发送模板消息
        -1	系统繁忙，此时请开发者稍候再试
        0	请求成功
        40001	AppSecret错误或者AppSecret不属于这个公众号，请开发者确认AppSecret的正确性
        40002	请确保grant_type字段值为client_credential
        40164	调用接口的IP地址不在白名单中，请在接口IP白名单中进行设置。
        89503	此IP调用需要管理员确认,请联系管理员
        89501	此IP正在等待管理员确认,请联系管理员
        89506	24小时内该IP被管理员拒绝调用两次，24小时内不可再使用该IP调用
        89507	1小时内该IP被管理员拒绝调用一次，1小时内不可再使用该IP调用
        """

        url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=" + self.get_token()
        data = {
            "touser": to_user,
            "template_id": template_id,
            "url": render_url,
            "data": template_data
        }
        json_tmp = json.dumps(data)
        for _ in range(self.max_retry):
            res = requests.post(url, data=json_tmp).json()
            if res['errcode'] == 0:
                logger.debug("模板消息发送成功")
                return None
            elif res['errcode'] == -1:
                logger.warning("模板消息发送失败,系统繁忙,稍后重试")
                time.sleep(10)
                continue
            else:
                logger.warning(f"errcode: {res['errcode']},message:{res['errmsg']},从新获取token")
                self.get_token_from_server()
                url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=" + self.get_token()
                continue
        logger.critical("超过做大重试次数,模板消息发送失败")

    def send_network_recovery_notification(self, to_user, render_url, fault_point, fault_time, recovery_time, remark):
        """发送网络恢复通知"""
        template_id = "rAyyL_VaKvmgVV8RvBIE44Wco52qbrXpU4XDhhsaw9s"
        template_data = {
            "first": {"value": "网络恢复通知"},
            "keyword1": {"value": fault_point},  # 故障点
            "keyword2": {"value": fault_time},  # 故障时间
            "keyword3": {"value": recovery_time},  # 恢复时间
            "remark": {"value": remark}
        }
        return self.__send_messages(to_user, template_id, render_url, template_data)

    def send_network_anomaly_notification(self, to_user, render_url, fault_time, fault_type, remark):
        """发送网络异常通知"""
        template_id = "ZYaxoViDeS-c23Iae3ivQLXZ_sTDZW82fFc2Ln92S_c"
        template_data = {
            "first": {"value": "网络异常通知"},
            "keyword1": {"value": fault_time},  # 异常时间
            "keyword2": {"value": fault_type},  # 异常类型
            "remark": {"value": remark}
        }
        return self.__send_messages(to_user, template_id, render_url, template_data)

    def send_network_outage_notification(self, to_user, render_url, fault_location, fault_time, remark):
        """发送网络中断通知"""
        template_id = "KZYN7KOcF-d0NWaGOahpnxjHOYZPCRtUVzb-mc8I_0U"
        template_data = {
            "first": {"value": "网络通知"},
            "keyword1": {"value": fault_location},  # 故障点
            "keyword2": {"value": fault_time},  # 故障时间
            "remark": {"value": remark}
        }
        return self.__send_messages(to_user, template_id, render_url, template_data)

    def send_abnormal_equipment_notification(self, to_user, render_url, equipment_type, equipment_name, fault_date,
                                             fault_location, fault_reason):
        """
        发送设备异常通知
        :param to_user:
        :param render_url:
        :param equipment_type:
        :param equipment_name:
        :param fault_date:
        :param fault_location:
        :param fault_reason:
        :return:
        """
        template_id = "Kgf4u_rucA5fp6qE3Q2p9GR05nlKCJdEdJTeTnkli90"
        template_data = {
            "thing4": {"value": equipment_type},  # 设备类型
            "thing8": {"value": "equipment_name"},  # 设备名
            "time9": {"value": fault_date},  # 故障日期
            "thing11": {"value": fault_location},  # 故障地点
            "thing6": {"value": fault_reason},  # 故障原因
        }
        return self.__send_messages(to_user, template_id, render_url, template_data)

    def send_fault_notify(self, message: dict):
        """发送故障通知"""
        to_user = message.get("recipient").get(self.name.lower())
        message['recipient_name'] = message.get("recipient").get("name")
        message['recipient_gender'] = "先生" if message.get("recipient").get("gender") == "male" else "女士"
        render_url = message.get('render_url', "www.baidu.com")  # 模版消息生效字段
        fault_time = message.get('fault_time')  # 模版消息生效字段
        fault_location = message.get('location', "请检查配置文件中的location字段")  # 模版消息生效字段
        remark = DEVICE_FAULT_MESSAGE_TEMPLATE.format(**message)
        self.send_network_outage_notification(to_user, render_url, fault_location, fault_time, remark)

    def send_recovery_notify(self, message: dict):
        """发送恢复通知"""
        to_user = message.get("recipient").get(self.name.lower())
        message['recipient_name'] = message.get("recipient").get("name")
        message['recipient_gender'] = "先生" if message.get("recipient").get("gender") == "male" else "女士"
        render_url = message.get('render_url', "www.baidu.com")  # 模版消息生效字段
        fault_time = message.get('fault_time')  # 模版消息生效字段
        recovery_time = message.get('recovery_time')  # 模版消息生效字段
        fault_location = message.get('location', "请检查配置文件中的location字段")  # 模版消息生效字段
        remark = DEVICE_FAULT_MESSAGE_TEMPLATE.format(**message)
        self.send_network_recovery_notification(to_user, render_url, fault_location, fault_time, recovery_time, remark)


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()
    msg = WeChatTemplateMessage()
    msg.send_network_recovery_notification("ozoJjv3QyBLlDf-PzkxfrRA5aPHk", "http://117.176.217.131:50000", "japan",
                                           "now", "never", "remark")
    msg.send_network_outage_notification("ozoJjv3QyBLlDf-PzkxfrRA5aPHk", "http://117.176.217.131:50000", "japan", "now",
                                         "test")
