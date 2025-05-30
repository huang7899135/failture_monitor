import calendar
import os
import pickle
from datetime import datetime
from typing import cast

import requests
import json
from abc import ABC, abstractmethod
from urllib3.exceptions import InsecureRequestWarning
from celery.utils.log import get_task_logger
from model.session import SessionLocal

logger = get_task_logger(__name__)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Platform(ABC):

    def __init__(self):
        self.platform_name = self.__class__.__name__.lower()
        # 动态获取session_file_path,当前路径的上一级目录的sessions目录
        self.session_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                              f"sessions/{self.platform_name}")
        self.session: requests.Session | None = None
        self.login_info = self.__load_config()["login_info"][self.platform_name]
        self.username = self.login_info["username"]
        self.password = self.login_info["password"]
        self.is_login = False

    def __bool__(self):
        return self.is_login

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def __load_config():
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(root_dir, "config", 'platform_config.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @abstractmethod
    def _login(self, *args, **kwargs):
        raise NotImplementedError

    def _logout(self, *args, **kwargs):
        raise NotImplementedError

    def _fetch(self, *args, **kwargs):
        """加载本地session,如果失败就从新登录"""
        resp = None
        if not self.session:
            logger.info("加载本地session失败,从新登录")
            self._login()
        for _ in range(3):
            try:
                self.session = cast(requests.Session, self.session)
                resp = self.session.post(*args, **kwargs, verify=False)
            except requests.exceptions.ConnectionError:
                pass
            else:
                break
        if resp is None:
            raise Exception("请求失败,请检查网络")
        if self.session_is_unexpected(resp):
            logger.info("session异常,重新登录")
            self._login()
            for _ in range(3):
                try:
                    resp = self.session.post(*args, **kwargs, verify=False)
                except requests.exceptions.ConnectionError:
                    pass
                else:
                    break
        return resp

    def _retrieve(self, *args, **kwargs):
        """自定义get请求方法,如果请求失败,则重新登录"""
        if not self.session:
            logger.info("加载本地session失败,从新登录")
            self._login()
        resp = self.session.get(*args, **kwargs, verify=False)
        logger.debug(f"fetch status_code:{resp.status_code}")
        if self.session_is_unexpected(resp):
            logger.info("session异常,重新登录")
            self._login()
            resp = self.session.get(*args, **kwargs, verify=False)
        return resp

    def init(self):
        self.session = self.load_session()

    def before_login(self):
        """
        登录前的准备工作,初始化session,并设置请求头
        :return: None
        """
        self.session = requests.Session()
        self.session.headers['Content-Type'] = 'application/json'
        self.session.verify = False

    def after_login(self):
        """登录成功后,修改登录状态,并保行保存session的工作"""
        self.is_login = True
        self.save_session()

    def session_is_unexpected(self, resp):
        """session是否符合预期"""
        if not resp.status_code == 200:
            logger.warning(f"session异常:状态码({resp.status_code}),content: {resp.text}")
            raise Exception(f"请求失败:{resp.status_code}")

    def load_session(self):
        """加载本地session"""
        if os.path.exists(self.session_file_path):
            with open(self.session_file_path, 'rb') as f:
                try:
                    ret = pickle.load(f)
                    logger.info(f"本地session({self.platform_name})加载成功")
                    return ret
                except Exception as e:
                    logger.warning(f"session加载出错:{e}")
                    return None
        logger.debug(f"本地暂无session文件")
        return None

    def save_session(self):
        """保存session到本地"""
        try:
            with open(self.session_file_path, 'wb') as f:
                pickle.dump(self.session, f)
        except Exception as e:
            logger.warning(f"session保存失败:{e}")
        logger.info("session保存成功")


class Billing95PercentilePlatform(Platform):
    def __init__(self):
        super().__init__()
        self.sql_session = None

    def __enter__(self):
        self.init()
        self.sql_session = SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sql_session.close()
        pass

    @abstractmethod
    def _login(self, *args, **kwargs):
        pass

    @staticmethod
    def get_current_month_days():
        """计算本月天数"""
        now = datetime.now()
        days = calendar.monthrange(now.year, now.month)[1]
        return days

    @abstractmethod
    def query_server_income_info(self) -> list:
        pass

    @abstractmethod
    def analyze_server_income(self, income_info: list) -> dict:
        """
        分析服务器收益
        :param income_info: 从query_server_revenue_status获取的服务器信息
        :return: {
            "problem_servers": [],
            "normal_servers": []}
        """
        pass

    def perform_income_check(self):
        """执行收入检查"""
        income_info = self.query_server_income_info()
        income_info = self.analyze_server_income(income_info)
        return income_info
