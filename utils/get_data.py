import yaml
import os
from config.setting import MONITOR_OBJECTS_DATA_SOURCE


def get_monitor_objects_from_yaml():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_dir = os.path.join(parent_dir, "datasource/monitor_objects.yaml")
    with open(config_dir, "r", encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def get_notification_recipients_from_yaml():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_dir = os.path.join(parent_dir, "datasource/notification_recipient_group.yaml")
    with open(config_dir, "r", encoding='utf-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def get_monitor_objects():
    if MONITOR_OBJECTS_DATA_SOURCE == "yaml":
        return get_monitor_objects_from_yaml()


def get_notification_recipients():
    if MONITOR_OBJECTS_DATA_SOURCE == "yaml":
        return get_notification_recipients_from_yaml()

