from .BasePlatform import Platform
import logging
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# logger = logging.getLogger(__name__)


class XunLei(Platform):
    def __init__(self):
        super().__init__()
        pass

    def _login(self):
        self.before_login()
        url = 'https://console.snodehome.cn/api/auth/login'
        data = {
            "username": self.username,
            "password": self.password
        }
        resp = self.session.post(url=url, json=data)
        if resp.json()['code'] == 0:
            token = resp.json()['data']['token']
            logger.debug(f"token:{token}")
            # 修改cookies,增加token的值
            self.session.cookies.set('token', token)
            self.session.cookies.set('account', self.username)
            self.after_login()
            logger.debug(resp.json())
            logger.info("迅雷:登录成功")
        else:
            logger.error(f"迅雷:{resp.json()['msg']}")
            raise Exception(resp.json()['msg'])

    def _logout(self):
        url = 'https://console.snodehome.cn/api/auth/logout'
        self.session.get(url=url)

    def query_server_status(self):
        """查询服务器状态"""
        url = "https://console.snodehome.cn/api/miner_manage/miner/minerList"
        resp = self._retrieve(url=url)
        if resp.json()['code'] == 0:
            ret = resp.json()['data']['list']
            return self.identify_server_status(ret)
        else:
            logger.error(f"迅雷:{resp.json()['msg']}")
            raise Exception(resp.json()['msg'])

    def session_is_unexpected(self, resp):
        try:
            super().session_is_unexpected(resp)
        except Exception as e:
            logger.error(e)
            return True
        if resp.json()['code'] == 10001:
            return True

    def generate_web_url(self, device_id):
        """根据device_id生成控制台url"""
        url = f"https://console.snodehome.cn/api/miner_manage/miner/generateWebUrl?device_id={device_id}"
        resp = self._retrieve(url=url)
        if resp.json()['code'] == 0:

            return resp.json()['data']['url']
        else:
            logger.error(f"迅雷:{resp.json()['msg']}")
            raise Exception(resp.json()['msg'])

    def query_device_pppoe_status(self, device_id):
        """获取设备pppoe状态,默认情况是多播线路,即mutidial下面的账号"""
        self.session.headers['referer'] = self.generate_web_url(device_id)
        url = f"http://{device_id}.localweb.snodehome.cn/api/pppoeStatus"
        resp = self.session.get(url=url)
        if resp.json()['code'] == 0:
            ret = resp.json()['data']['multidial']
            return self.identify_account_status(ret)
        else:
            logger.error(f"迅雷:{resp.json()['msg']}")
            raise Exception(resp.json()['msg'])

    @staticmethod
    def identify_account_status(data: list) -> dict:
        """识别账号状态"""
        ret = {
            "connected": [],
            "disconnected": []
        }
        for account in data:
            if account['status'] == "connected":
                ret['connected'].append(account)
            else:
                ret['disconnected'].append(account)
        return ret

    @staticmethod
    def identify_server_status(data: list) -> dict:
        """识别服务器状态"""
        ret = {
            "online": [],
            "offline": [],
            "review": [],
            "clear": []
        }
        for server in data:
            if server['miner_status'] == 2:
                ret['online'].append(server)
            elif server['miner_status'] == 5:
                ret['offline'].append(server)
            elif server['miner_status'] == 6:
                ret['clear'].append(server)
            else:
                ret['review'].append(server)
        return ret

    def query_online_device_fault_account(self):
        """查询在线设备的账号状态"""
        fault_server = []
        ret = self.query_server_status()
        online_server = ret['online']
        for server in online_server:
            device_id = server['device_id']
            ret = self.query_device_pppoe_status(device_id)
            if ret['disconnected']:
                logger.warning(f"设备{device_id}有故障账号:{ret['disconnected']}")
                logger.warning(f"url: {self.session.headers['referer']}#/pppoe/state")
                fault_server.append({
                    "device_id": device_id,
                    "fault_account": ret['disconnected'],
                    "url": self.session.headers['referer'] + "#/pppoe/state"
                })


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()

    xunlei = XunLei()
    xunlei.query_online_device_fault_account()
    # # ret = xunlei.query_device_pppoe_status("XYBM5FL9F1VXK5BL")
    # ret = xunlei.query_server_status()
    # online_server = ret['online']
    # for server in online_server:
    #     device_id = server['device_id']
    #     ret = xunlei.query_device_pppoe_status(device_id)
    #     if ret['disconnected']:
    #         logger.info(f"设备{device_id}有故障账号:{ret['disconnected']}")
    #         logger.info(f"url: {xunlei.session.headers['referer']}#/pppoe/state")
