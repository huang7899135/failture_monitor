import time
from .BasePlatform import Platform
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# logger = logging.getLogger(__name__)


class Openfog(Platform):
    def _login(self, *args, **kwargs):
        self.before_login()
        url = "https://api.webrtc.win/v1/vdn/login"
        data = {
            "username": self.login_info["username"],
            "password": self.login_info["password"],
        }
        resp = self.session.post(url=url, json=data)
        if resp.status_code == 200:
            # 保存token
            self.session.headers['X-Pear-Token'] = resp.json().get("token")
            self.session.headers['X-Pear-User'] = str(resp.json().get("user_id"))
            self.after_login()
            logger.debug(resp.json())
            logger.info("openfog:登录成功")

    def query_historical_income(self):
        query_url = "https://nmsapi.webrtc.win/expected/history"
        query_data = {
            "from": 0,
            "to": 20
        }
        resp = self._retrieve(query_url, params=query_data)
        if resp.status_code == 200:
            return self.reformat_historical_income(resp.json())
        else:
            raise Exception(f"查询失败:{resp.status_code}")

    @staticmethod
    def convert_timestamp_to_date(timestamp: int) -> str:
        """
        将时间戳转换为datetimez字符串
        :param timestamp:
        :return:日期字符串
        """
        return time.strftime("%Y-%m-%d", time.localtime(timestamp))

    def reformat_historical_income(self, data: list) -> list:
        """
        将爬取到的数据进行格式化
        :param data:list,爬取到的数据
        :return:转换后的数据
        """
        reformatted_data = []
        for item in data:
            item['cash'] = item['cash'] / 100
            item["date"] = self.convert_timestamp_to_date(item.get("time"))
            reformatted_data.append(item)
        return reformatted_data


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger
    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()

    fog = Openfog()
    bills = fog.query_historical_income()
    print(bills)
