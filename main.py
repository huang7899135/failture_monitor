from monitor.monitor import DevicesMonitor
from utils.logger import setup_logger
import os

# 设置当前目录为工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


logger = setup_logger()

if __name__ == "__main__":

    monitor = DevicesMonitor()
    monitor.run()

