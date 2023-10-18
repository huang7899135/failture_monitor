import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


def setup_logger():
    app_env = os.environ.get('APP_ENV', 'dev')  # 默认为 'development'
    debug = app_env == 'dev'

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter('%(lineno)4d [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

    # 确保 log 文件夹存在,log文件夹位于项目文件的同级目录

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 在开发环境中，使用屏幕和日志输出
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        file_handler = TimedRotatingFileHandler('log/debug.log', when="midnight")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    # 在生产环境中，使用日志文件
    else:
        formatter = logging.Formatter('%(asctime)s %(lineno)4d [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        log_filename = datetime.now().strftime("%Y-%m-%d.log")
        log_filepath = os.path.join(log_dir, log_filename)
        file_handler = TimedRotatingFileHandler(log_filepath, when="midnight")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    logger = setup_logger()
    logger.info("This is an info message.")
    logger.debug("This is a debug message.")


