from model.session import SessionLocal, engine
from model.models import Group, Devices, User, UserNotifyConfig
import yaml
from model import create_tables
from sqlalchemy import MetaData, Table, inspect

# 先判断是否存在数据库
inspector = inspect(engine)
create_table_list = {"groups", "devices", "users", "user_notify_configurations", "failure_tickets",
                     "user_notify_frequency"}

if bool(create_table_list & set(inspector.get_table_names())):
    raise Exception("Table exists.")

# 空白数据库创建书库表
create_tables()

with open("datasource/source.yaml", "r") as file:
    data = yaml.safe_load(file)

# Insert the data into the database
session = SessionLocal()

group_objects = {}
for group_data in data.get("groups"):
    group = Group(name=group_data['name'])
    session.add(group)
    session.flush()  # To get the ID after insertion
    group_objects[group.name] = group

# Insert users and their associations with groups
for user_data in data.get("users"):
    user = User(name=user_data['name'], gender=user_data['gender'])
    user.groups = [group_objects[group_name] for group_name in user_data['groups']]
    session.add(user)
    session.flush()

# Insert user_notify_configurations
for config_data in data.get("user_notify_configurations"):
    user = session.query(User).filter_by(name=config_data['user']).first()
    config = UserNotifyConfig(
        user_id=user.id,
        notify_method=config_data['notify_method'],
        user_value=config_data['user_value'],
        is_enable=config_data['is_enable']
    )
    session.add(config)

# Insert devices
for device_data in data.get("devices"):
    group = group_objects.get(device_data['notify_group'])
    device = Devices(
        name=device_data['device'],
        location=device_data['location'],
        device_type=device_data['device_type'],
        is_enable=device_data['is_effective'],
        address=device_data['address'],
        port=device_data.get('port'),
        check_method=device_data['check_method'],
        group_id=group.id if group else None
    )
    session.add(device)

# 4. Commit the changes
session.commit()
session.close()
