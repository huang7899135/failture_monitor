import os
import pickle
from model.models import IncomeMonitorServer
from .BasePlatform import Billing95PercentilePlatform
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class HaiDian(Billing95PercentilePlatform):
    def __init__(self):
        super().__init__()
        self.platform_cn_name = "海点云"
        self.token = self.load_token()
        self.number_of_servers_per_page = 10

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

    def query_servers_number(self) -> int:
        """
        查询服务器数量
        :return: 服务器数量
        """
        query_url = "https://s.haidiancloud.com/pcdnmapi/s20602"
        query_data = {
            "owner_name": self.login_info["username"],
            "token": self.token
        }
        resp = self._fetch(query_url, json=query_data)
        logger.debug(resp.json())
        if resp.json().get("status") == 0:
            return int(resp.json().get("result").get("all_num"))
        else:
            logger.error(f"haidian:{resp.json().get('msg')}")
            raise Exception(resp.json().get('msg'))

    def calculate_query_offset(self) -> int:
        """
        计算翻页数量
        :return:
        """
        servers_number = self.query_servers_number()
        return servers_number // self.number_of_servers_per_page + 1

    def _query_server_income_info(self, offset: int) -> list:
        """查询服务器收入状态"""
        query_url = "https://s.haidiancloud.com/pcdnmapi/s20601"
        query_data = {
            "owner_name": self.login_info["username"],
            "offset": offset,
            "search_word": "",
            "status_val": 1,
            "token": self.token
        }
        resp = self._fetch(query_url, json=query_data)
        logger.debug(resp.json())
        if resp.json().get("status") == 0:
            return resp.json().get("result").get("data")
        else:
            logger.error(f"haidian:{resp.json().get('msg')}")
            raise Exception(resp.json().get('msg'))

    def query_server_income_info(self) -> list:
        """查询服务器收入状态"""
        offset = self.calculate_query_offset()
        income_info = []
        for i in range(1, offset + 1):
            income_info.extend(self._query_server_income_info(i))
        return income_info

    def analyze_server_income(self, income_info: list) -> dict:
        """
        分析服务器收益
        :param income_info: 从query_server_revenue_status获取的服务器信息
        :return: {
            "problem_servers": [],
            "normal_servers": []}
        """
        exception_map = {
            "设备状态异常": "服务器疑似被下架或者离线",
            "设备收入异常": "income值低于expected值"
        }
        problem_servers = []
        for server in income_info:
            flat = False
            device_sn = server.get("device_sn")
            device_obj = self.sql_session.query(IncomeMonitorServer).filter(
                IncomeMonitorServer.device_sn == device_sn).first()

            bandwidth = self.convert_bandwidth_to_mb(server.get("bandwidth_up"))
            device_status = server.get("device_status")
            yesterday_profit = server.get("yesterday_profit")
            remark = server.get("remark")
            exception_type = ""
            expected_income = bandwidth * 1 / self.get_current_month_days()
            if device_obj:
                if not device_obj.is_enable:
                    continue
                if device_obj.expected_income:
                    expected_income = device_obj.expected_income

            if expected_income > yesterday_profit:
                flat = True
                # 如果description不为空则加入新加一行到底部

                exception_type = f"设备收入异常:{int(yesterday_profit)}<{int(expected_income)}"

            if device_status != "0":
                flat = True
                exception_type = f"设备状态异常:{int(yesterday_profit)}<{int(expected_income)}"

            if flat:
                logger.debug(
                    f"haidian:{device_sn}:({remark})异常,昨日收入{yesterday_profit}元,预期收入{expected_income}元")
                problem_servers.append({
                    "exception_type": exception_type,
                    "exception_reason": exception_map.get(exception_type, None),
                    # 如果没有device_obj.group_id则为1
                    "group_id": device_obj.group_id if device_obj else 1,
                    "equipment_name": f"{self.platform_cn_name}:{remark}"
                })
        normal_servers = list(filter(lambda x: x not in problem_servers, income_info))
        return {
            "problem_servers": problem_servers,
            "normal_servers": normal_servers
        }

