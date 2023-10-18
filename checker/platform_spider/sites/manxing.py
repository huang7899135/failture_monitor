import logging
import time
import requests
from .BasePlatform import Platform
from utils.crypto import md5_encrypt

logger = logging.getLogger(__name__)


class ManXing(Platform):
    def __init__(self):
        super().__init__()
        self.query_url = "https://service.chxyun.cn/client/msg/list"

    def session_is_unexpected(self, resp):
        try:
            super().session_is_unexpected(resp)
        except Exception as e:
            logger.error(e)
            return True
        if resp.json()['code'] == -2:
            return True

    def login(self):
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

    def logout(self):
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
        resp = self.fetch(url=self.query_url, json=data)
        logger.debug(resp.json())
        return resp.json()

    def query_accounts_status_by_server_id(self, server_id):
        url = "https://service.chxyun.cn/client/node/info"
        data = {
            "id": server_id
        }
        resp = self.fetch(url=url, json=data)
        account_list = resp.json()['data']['gather']['dial']
        logger.debug(account_list)
        return account_list

    def query_fault_accounts(self) -> dict:
        """查询故障账号,默认1000条"""
        pass

    def auto_recover_accounts(self):
        """自动恢复故障"""
        pass


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger

    os.environ['APP_ENV'] = "dev"

    logger = setup_logger()
    manxin = ManXing()
    manxin.query_server_status()
    manxin.query_accounts_status_by_server_id(41185)
