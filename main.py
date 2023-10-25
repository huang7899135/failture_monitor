from monitor.device_monitor import DevicesMonitor
from utils.logger import setup_logger
import os

# 设置当前目录为工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


logger = setup_logger()

if __name__ == "__main__":
    import os
    from utils.logger import setup_logger

    os.environ['APP_ENV'] = "dev"
    logger = setup_logger()
    monitor = DevicesMonitor()
    monitor.run()

