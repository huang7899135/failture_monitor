import logging
import time
import os
from .BasePlatform import Platform
from pprint import pprint
import pickle
from celery.utils.log import get_task_logger
import calendar
import datetime

logger = get_task_logger(__name__)


# logger = logging.getLogger(__name__)


class Haidian(Platform):
    def __init__(self):
        super().__init__()
        self.token = self.load_token()

    def _login(self, *args, **kwargs):
        self.before_login()
        url = "https://s.haidiancloud.com/pcdnmapi/s3"
        login_data = {
            "owner_name": self.login_info["username"],
            "owner_phone": self.login_info["username"],
            "owner_passwd": self.login_info["password"],
            "phone_vcode": "",
            "vcode": ""
        }
        resp = self.session.post(url, json=login_data)
        if resp.status_code == 200 and resp.json().get("status") == 0:
            self.token = resp.json().get("result").get("token")
            self.after_login()
            logger.debug(resp.json())
            logger.info("haidian:登录成功")
        else:
            logger.error(f"haidian:{resp.json().get('msg')}")
            raise Exception(resp.json().get('msg'))

    def load_token(self):
        token_file_path = os.path.join(os.path.dirname(self.session_file_path), "haidian_token")
        if os.path.exists(token_file_path):
            with open(token_file_path, 'rb') as f:
                try:
                    token = pickle.load(f)
                    return token
                except Exception as e:
                    logger.error(e)
        else:
            self._login()
            return self.token

    def save_token(self):
        token_file_path = os.path.join(os.path.dirname(self.session_file_path), "haidian_token")
        with open(token_file_path, 'wb') as f:
            pickle.dump(self.token, f)

    def after_login(self):
        super().after_login()
        self.save_token()

    def session_is_unexpected(self, resp):
        super().session_is_unexpected(resp)
        if resp.json()['status'] == 1:
            return True

    def query_server_revenue_status(self):
        """查询服务器状态"""
        query_url = "https://s.haidiancloud.com/pcdnmapi/s2060"
        query_data = {
            "owner_name": self.login_info["username"],
            "offset": "0",
            "search_word": "",
            "token": self.token
        }
        resp = self._fetch(query_url, json=query_data)
        logger.debug(resp.json())
        return resp.json()

    # 计算本月天数
    @staticmethod
    def get_current_month_days():
        now = datetime.datetime.now()
        days = calendar.monthrange(now.year, now.month)[1]
        return days

    def find_low_income_server(self, server_info: list):
        """查找低收入服务器"""
        problem_servers = []
        for server in server_info:
            flat = False
            # 提取带宽数据
            bandwidth = self.convert_bandwidth_to_mb(server.get("bandwidth_up"))
            device_sn = server.get("device_sn")
            device_status = server.get("device_status")
            yesterday_profit = server.get("yesterday_profit")
            remark = server.get("remark")
            description = ""
            if device_status != "0":
                flat = True
                description = f"设备状态异常"
            # 预期收入等于每M带宽1元一个月
            expected_income = bandwidth * 1 / self.get_current_month_days()

            if expected_income > yesterday_profit:
                flat = True
                # 如果description不为空则加入新加一行到底部
                if description:
                    description += f"\n预期最低收入{expected_income}元，昨日收入{yesterday_profit}元"
                else: # 否则直接赋值
                    description = f"预期最低收入{expected_income}元，昨日收入{yesterday_profit}元"
            if flat:
                problem_servers.append({
                    "device_sn": device_sn,
                    "description": description,
                    "remark": remark
                })
        return problem_servers

    @staticmethod
    def convert_bandwidth_to_mb(bandwidth_str):
        # Dictionary to store conversion factors
        conversion_factors = {'G': 1024, 'M': 1, 'K': 1 / 1024}

        # Extracting the numerical part and the unit
        # Updated to include decimal points
        value = ''.join(filter(lambda x: x.isdigit() or x == '.', bandwidth_str))
        unit = ''.join(filter(str.isalpha, bandwidth_str)).upper()

        # Convert the value to a float and then to an integer after applying conversion factor
        value_in_mb = int(float(value) * conversion_factors.get(unit, 0))

        return value_in_mb

    def auto_check_server_revenue(self):
        """自动检查服务器收益"""
        server_info = self.query_server_revenue_status().get("result").get("data")
        problem_servers = self.find_low_income_server(server_info)
        if problem_servers:
            [print(server) for server in problem_servers]
            # self.send_wechat_message(problem_servers)
        else:
            logger.info("haidian:服务器收益正常")
