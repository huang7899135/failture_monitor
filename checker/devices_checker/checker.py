import logging
import os
import socket
import subprocess
import asyncio
import aiohttp
import aioping
import requests
import time
from datetime import datetime
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class AsyncDeviceOnlineChecker:

    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.check_method = kwargs.get("check_method")
        self.address = kwargs.get("address")
        self.port = kwargs.get("port")
        self.max_retry = kwargs.get("max_retry", 3)

    async def __check_via_icmp(self):
        try:
            await aioping.ping(self.address, timeout=3)
            return True
        except TimeoutError:
            return False

    async def __check_via_tcp(self):
        reader, writer = None, None
        try:
            reader, writer = await asyncio.open_connection(self.address, int(self.port))
            writer.close()
            return True
        except (TimeoutError, ConnectionRefusedError, OSError):
            return False
        finally:
            if writer:
                writer.close()

    async def __check_via_http(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"http://{self.address}:{self.port}", timeout=3) as response:
                    if response.status == 200:
                        return True
                    return False
            except (asyncio.exceptions.TimeoutError, ConnectionRefusedError, aiohttp.ClientConnectorError):
                return False

    @property
    def __check_method_func(self):
        if self.check_method == "icmp":
            return self.__check_via_icmp
        elif self.check_method == "tcp":
            assert self.port, "Port must be specified when using TCP check"
            return self.__check_via_tcp
        elif self.check_method == "http":
            return self.__check_via_http
        else:
            raise ValueError("Check method can only be icmp/tcp/http")

    async def check(self):
        for _ in range(self.max_retry):
            flat = await self.__check_method_func()
            if flat:
                self.kwargs["is_online"] = True
                return self.kwargs
        self.kwargs["is_online"] = False
        self.kwargs["fault_time"] = datetime.now()
        return self.kwargs


class DeviceOnlineChecker:

    def __init__(self, check_method: str, address: str, port: str = "", max_retry: int = 3):
        """
        检测设备类型目前支持icmp/tcp/http
        :param check_method: 设备检测方式
        :param address: 设备ip地址
        :param port: 端口
        :param max_retry:重试次数,越大越精确,耗费的时间越多
        """
        self.check_method = check_method
        self.address = address
        self.port = port
        self.max_retry = max_retry

    def __check_via_icmp(self):
        """利用ping的请求,来检测是否在线"""
        try:
            subprocess.run(["ping", "-c", "3", self.address], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=True)
            return True  # 通
        except subprocess.CalledProcessError:
            return False  # 不通

    def __check_via_tcp(self):
        """利用socket模拟tcp连接,来检测是否在线"""
        try:
            socket.setdefaulttimeout(3)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.address, int(self.port)))
            s.close()
            return True  # 通
        except socket.timeout:
            return False  # 不通
        except ConnectionRefusedError:
            return False

    def __check_via_http(self):
        """利用requests模拟http请求,来检测是否在线"""
        try:
            requests.get(f"http://{self.address}:{self.port}", timeout=3)
            return True  # 通
        except requests.exceptions.ConnectTimeout:
            return False  # 不通
        except requests.exceptions.ConnectionError:
            return False  # 不通

    @property
    def __check_method_func(self):
        if self.check_method == "icmp":
            return self.__check_via_icmp
        elif self.check_method == "tcp":
            assert self.port, "使用tcp检测时,必须指定端口"
            return self.__check_via_tcp
        elif self.check_method == "http":
            return self.__check_via_http
        else:
            raise ValueError("type只能是icmp/port/request")

    def check(self):
        for _ in range(self.max_retry):
            if self.__check_method_func():
                return True
        return False


async def async_checker(target_list: list) -> tuple:
    """传入target_list,执行检测,然后返回结果,target_list的格式为[(check_method, address, port), ...]"""

    tasks = []
    for target_obj in target_list:
        tasks.append(AsyncDeviceOnlineChecker(target_obj))
    return await asyncio.gather(*[task.check() for task in tasks])


def perform_async_check_devices(target_list: list) -> tuple:
    """异步转换同步,检测设备是否在线,返回结果,结果格式为"""

    return asyncio.run(async_checker(target_list))


if __name__ == "__main__":
    import os
    from utils.logger import setup_logger

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()
    s = time.time()
    ip_list = []
    # for i in range(0, 20):  # 3rd octet
    #     for j in range(1, 256):  # 4th octet
    #         ip = f"117.176.{i}.{j}"
    #         ip_list.append({
    #             "check_method": "tcp",
    #             "address": ip,
    #             "port": 22})
    target = [
        {"check_method": "icmp", "address": "223.87.234.3"},
        {"check_method": "icmp", "address": "223.87.234.2"},
        {"check_method": "icmp", "address": "223.87.234.4"},
        {"check_method": "icmp", "address": "223.87.234.5"},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 22},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 50000},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 7000},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 7002},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 7003},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 6700},
        {"check_method": "tcp", "address": "117.176.217.131", "port": 25},

    ]
    ret = perform_async_check_devices(target)
    print(ret)
    print(time.time() - s)
