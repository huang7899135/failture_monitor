import os

env = os.getenv('ENV', 'prod')

if env == 'prod':
    from config.setting_prod import *
else:
    from config.setting_dev import *
