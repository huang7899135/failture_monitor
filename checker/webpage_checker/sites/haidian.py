import logging
import time
import os
from .BasePlatform import Platform
from pprint import pprint
import pickle
from celery.utils.log import get_task_logger

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

    # def init(self):
    #     super().init()

    def query_server_status(self):
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
