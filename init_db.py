import time
import sys
from model.session import engine # Only engine is needed for create_tables
from model import create_tables

def wait_for_db(max_retries=30, delay=2):
    """等待数据库连接可用"""
    for attempt in range(max_retries):
        try:
            # 尝试连接数据库
            connection = engine.connect()
            connection.close()
            print(f"✓ 数据库连接成功 (尝试 {attempt + 1}/{max_retries})")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ 等待数据库连接... (尝试 {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                print(f"❌ 数据库连接失败，已尝试 {max_retries} 次")
                print(f"错误信息: {e}")
                return False
    return False

# 等待数据库连接
if not wait_for_db():
    print("❌ 无法连接到数据库，退出初始化")
    sys.exit(1)

# Create all tables defined in models.py (linked via Base)
# This function handles checking for existing tables, so no need for manual checks here.
try:
    create_tables()
    print("✓ 数据库表结构检查/创建完成")
except Exception as e:
    print(f"❌ 数据库表创建失败: {e}")
    sys.exit(1)

# The following data population part remains commented out for now.
# If you want to enable it, ensure the YAML file path is correct
# and consider if it should run every time or only on a truly empty DB.

# import yaml
# from model.session import SessionLocal
# from model.models import Group, Devices, User, UserNotifyConfig # Import all necessary models

# with open("datasource/source.yaml", "r") as file:
#     data = yaml.safe_load(file)
#
# # Insert the data into the database
# session = SessionLocal()
#
# group_objects = {}
# for group_data in data.get("groups"):
#     group = Group(name=group_data['name'])
#     session.add(group)
#     session.flush()  # To get the ID after insertion
#     group_objects[group.name] = group
#
# # Insert users and their associations with groups
# for user_data in data.get("users"):
#     user = User(name=user_data['name'], gender=user_data['gender'])
#     user.groups = [group_objects[group_name] for group_name in user_data['groups']]
#     session.add(user)
#     session.flush()
#
# # Insert user_notify_configurations
# for config_data in data.get("user_notify_configurations"):
#     user = session.query(User).filter_by(name=config_data['user']).first()
#     config = UserNotifyConfig(
#         user_id=user.id,
#         notify_method=config_data['notify_method'],
#         user_value=config_data['user_value'],
#         is_enable=config_data['is_enable']
#     )
#     session.add(config)
#
# # Insert devices
# for device_data in data.get("devices"):
#     group = group_objects.get(device_data['notify_group'])
#     device = Devices(
#         name=device_data['device'],
#         location=device_data['location'],
#         device_type=device_data['device_type'],
#         is_enable=device_data['is_effective'],
#         address=device_data['address'],
#         port=device_data.get('port'),
#         check_method=device_data['check_method'],
#         group_id=group.id if group else None
#     )
#     session.add(device)
#
# # 4. Commit the changes
# session.commit()
# session.close()
# print("Initial data populated (if uncommented and source.yaml exists).")
