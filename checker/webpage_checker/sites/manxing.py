from pprint import pprint
from model.models import IncomeMonitorServer
from .BasePlatform import Billing95PercentilePlatform
from utils.crypto import md5_encrypt
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# logger = logging.getLogger(__name__)


class ManXing(Billing95PercentilePlatform):

    def query_server_income_info(self) -> list:
        return self.query_server_status()

    def __init__(self):
        super().__init__()
        self.query_url = "https://service.chxyun.cn/client/msg/list"
        self.platform_cn_name = "漫星"

    def session_is_unexpected(self, resp):
        try:
            super().session_is_unexpected(resp)
        except Exception as e:
            logger.error(e)
            return True
        if resp.json()['code'] == -2:
            return True

    def _login(self):
        self.before_login()
        url = "https://service.chxyun.cn/client/user/login"
        data = {
            "username": self.login_info["username"],
            "password": md5_encrypt(self.login_info["password"]),
            "remember": True
        }
        resp = self.session.post(url=url, json=data)
        if resp.json()['code'] == 200:
            # 保存token
            token = resp.json()['data']['jwt_token']
            self.session.headers['Authorization'] = f"Bearer {token}"
            self.after_login()
            logger.debug(resp.json())
            logger.info("漫星:登录成功")
        else:
            logger.error(f"漫星:{resp.json()['msg']}")
            raise Exception(resp.json()['msg'])

    def _logout(self):
        pass

    def query_server_status(self):
        """查询服务器状态"""
        data = {
            "mac": "",
            "status_id": 0,
            "pageNumber": 1,
            "page": 1,
            "pageSize": 100
        }
        url = "https://service.chxyun.cn/client/node/list"
        resp = self._fetch(url=url, json=data)
        logger.debug(resp.json())
        if resp.json()['code'] == 200:
            return resp.json()['data']['list']
        else:
            raise Exception(resp.json()['msg'])

    def query_accounts_status_by_server_id(self, server_id):
        url = "https://service.chxyun.cn/client/node/info"
        data = {
            "id": server_id
        }
        resp = self._fetch(url=url, json=data)
        account_list = resp.json()['data']['gather']['dial']
        logger.debug(account_list)

        # pprint(account_list)
        return account_list

    def query_fault_accounts(self) -> dict:
        """查询故障账号,默认1000条"""
        pass

    def auto_recover_accounts(self):
        """自动恢复故障"""
        pass

    def analyze_server_income(self, income_info: list) -> dict:
        """
        漫星云只分析了服务器的状态
        :param income_info:
        :return:
        """
        problem_servers = []
        for server in income_info:
            device_sn = server.get("mac")
            try:
                device_obj = self.sql_session.query(IncomeMonitorServer).filter(
                    IncomeMonitorServer.device_sn == device_sn).first()
            except Exception as e:
                continue

            if not device_obj:
                continue
            else:
                if not device_obj.is_enable:
                    continue
            if server['status_id'] != 1:

                problem_servers.append({
                    "exception_type": f"服务器{server['status']}",
                    "exception_reason": "服务器疑似被下架或者离线",
                    # 如果没有device_obj.group_id则为1
                    "group_id": device_obj.group_id if device_obj else 1,
                    "equipment_name": f"{self.platform_cn_name}:{server['remark']}"
                })
                logger.debug(f"漫星:{device_sn}:({server['remark']})异常,状态:{server['status']}")
        return {
            "problem_servers": problem_servers,
            "normal_servers": []
        }




if __name__ == "__main__":
    import os
    from utils.logger import setup_logger

    os.environ['APP_ENV'] = "dev"

    logger = setup_logger()
    manxin = ManXing()
    manxin.query_server_status()
    manxin.query_accounts_status_by_server_id(41185)
