from sqlalchemy import Column, Integer, String, Sequence, Enum, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.orm import relationship
from model.base import Base
from datetime import datetime

user_group_association = Table('user_group', Base.metadata,
                               Column('user_id', Integer, ForeignKey('users.id')),
                               Column('group_id', Integer, ForeignKey('groups.id'))
                               )


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    gender = Column(Enum('male', 'female', name='gender_enum'), default='male', nullable=True)
    groups = relationship('Group', secondary=user_group_association, back_populates='users')


class UserNotifyConfig(Base):
    __tablename__ = 'user_notify_configurations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref='notify_config')
    notify_method = Column(String(50))
    user_value = Column(String(50))
    is_enable = Column(Boolean, default=True, nullable=True)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    users = relationship('User', secondary=user_group_association, back_populates='groups')


class Devices(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    location = Column(String(50))
    is_enable = Column(Boolean, default=True, nullable=True)
    device_type = Column(String(50))
    address = Column(String(100))
    port = Column(String(6), nullable=True)
    check_method = Column(Enum('icmp', 'tcp', 'http', name='check_method_enum'), default='icmp')
    group_id = Column(Integer, ForeignKey('groups.id'))  # 外键
    group = relationship('Group', backref='devices')  # 定义orm关系


class FailureTicket(Base):
    __tablename__ = 'failure_tickets'

    id = Column(Integer, Sequence('failure_ticket_id_seq'), primary_key=True)
    is_accepted = Column(Boolean, default=True, nullable=True)  # 是否受理
    is_done = Column(Boolean, default=True, nullable=True)  # 是否处理完成
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)
    device = relationship('Devices', backref='failure_tickets')
    platform_account = Column(String(50), nullable=True)
    platform_device = Column(String(50), nullable=True)
    platform_node = Column(String(50), nullable=True)
    fault_time = Column(DateTime, default=datetime.utcnow)
    recovery_time = Column(DateTime, nullable=True)
    # 处理人
    handler_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    handler = relationship('User', backref='failure_tickets')
    description = Column(String(1000), nullable=True)


class UserNotifyFrequency(Base):
    __tablename__ = 'user_notify_frequency'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref='user_notify_configurations')
    failure_ticket_id = Column(Integer, ForeignKey('failure_tickets.id'))
    failure_ticket = relationship('FailureTicket', backref='user_notify_configurations')
    message_is_read = Column(Boolean, default=False, nullable=True)
    next_notify_time = Column(DateTime)


class IncomeMonitorServer(Base):
    """收入监控服务器"""
    __tablename__ = 'income_monitor_servers'

    id = Column(Integer, primary_key=True)
    is_enable = Column(Boolean, default=True, nullable=True)
    device_sn = Column(String(50))
    platform = Column(String(50))
    expected_income = Column(Integer)
    remark = Column(String(50))
    group_id = Column(Integer, ForeignKey('groups.id'))
    group = relationship('Group', backref='income_monitor_servers')
    description = Column(String(1000), nullable=True)


class IncomeMonitorPlatform(Base):
    """收入监控平台"""
    __tablename__ = 'income_monitor_platforms'

    id = Column(Integer, primary_key=True)
    is_enable = Column(Boolean, default=True, nullable=True)
    platform = Column(String(50))  # 平台名称,需要跟类的名字保持一致,如Baishan,HaiDian
    description = Column(String(1000), nullable=True)
