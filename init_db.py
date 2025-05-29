#!/usr/bin/env python3
"""
数据库初始化脚本
功能：
1. 创建数据库表结构
2. 从 source.yaml 导入数据到数据库（增量更新）
"""

import sys
import os
import yaml
import argparse
from typing import Dict, List, Any

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model.base import Base
from model.models import User, Group, UserNotifyConfig, Devices
from model.session import engine, get_session
from utils.logger import setup_logger

# 设置日志
logger = setup_logger()


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, yaml_file_path: str = "datasource/source.yaml"):
        self.yaml_file_path = yaml_file_path
        
    def create_tables(self):
        """创建数据库表结构"""
        try:
            logger.info("开始创建数据库表结构...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ 数据库表结构创建完成")
        except Exception as e:
            logger.error(f"❌ 创建数据库表结构失败: {e}")
            raise
    
    def load_yaml_data(self) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        try:
            with open(self.yaml_file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            logger.info(f"✅ 成功加载配置文件: {self.yaml_file_path}")
            return data
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}")
            raise
    
    def sync_groups(self, groups_data: List[Dict], session) -> Dict[str, int]:
        """同步用户组数据（增量更新）"""
        logger.info("开始同步用户组数据...")
        group_name_to_id = {}
        
        for group_data in groups_data:
            group_name = group_data['name']
            
            # 检查组是否已存在
            existing_group = session.query(Group).filter_by(name=group_name).first()
            
            if existing_group:
                logger.debug(f"用户组 '{group_name}' 已存在，跳过")
                group_name_to_id[group_name] = existing_group.id
            else:
                # 创建新组
                new_group = Group(name=group_name)
                session.add(new_group)
                session.flush()  # 获取ID
                group_name_to_id[group_name] = new_group.id
                logger.info(f"✅ 创建新用户组: {group_name}")
        
        return group_name_to_id
    
    def sync_users(self, users_data: List[Dict], group_name_to_id: Dict[str, int], session) -> Dict[str, int]:
        """同步用户数据（增量更新）"""
        logger.info("开始同步用户数据...")
        user_name_to_id = {}
        
        for user_data in users_data:
            user_name = user_data['name']
            gender = user_data.get('gender', 'male')
            user_groups = user_data.get('groups', [])
            
            # 检查用户是否已存在
            existing_user = session.query(User).filter_by(name=user_name).first()
            
            if existing_user:
                logger.debug(f"用户 '{user_name}' 已存在，更新信息")
                # 更新用户信息
                existing_user.gender = gender
                
                # 更新用户组关联
                existing_user.groups.clear()
                for group_name in user_groups:
                    if group_name in group_name_to_id:
                        group = session.query(Group).get(group_name_to_id[group_name])
                        existing_user.groups.append(group)
                
                user_name_to_id[user_name] = existing_user.id
                logger.info(f"✅ 更新用户: {user_name}")
            else:
                # 创建新用户
                new_user = User(name=user_name, gender=gender)
                session.add(new_user)
                session.flush()  # 获取ID
                
                # 添加用户组关联
                for group_name in user_groups:
                    if group_name in group_name_to_id:
                        group = session.query(Group).get(group_name_to_id[group_name])
                        new_user.groups.append(group)
                
                user_name_to_id[user_name] = new_user.id
                logger.info(f"✅ 创建新用户: {user_name}")
        
        return user_name_to_id
    
    def sync_user_notify_configs(self, notify_configs_data: List[Dict], user_name_to_id: Dict[str, int], session):
        """同步用户通知配置（增量更新）"""
        logger.info("开始同步用户通知配置...")
        
        for config_data in notify_configs_data:
            user_name = config_data['user']
            notify_method = config_data['notify_method']
            user_value = config_data['user_value']
            is_enable = config_data.get('is_enable', True)
            
            if user_name not in user_name_to_id:
                logger.warning(f"⚠️ 用户 '{user_name}' 不存在，跳过通知配置")
                continue
            
            user_id = user_name_to_id[user_name]
            
            # 检查配置是否已存在
            existing_config = session.query(UserNotifyConfig).filter_by(
                user_id=user_id,
                notify_method=notify_method
            ).first()
            
            if existing_config:
                # 更新现有配置
                existing_config.user_value = user_value
                existing_config.is_enable = is_enable
                logger.info(f"✅ 更新用户 '{user_name}' 的 {notify_method} 通知配置")
            else:
                # 创建新配置
                new_config = UserNotifyConfig(
                    user_id=user_id,
                    notify_method=notify_method,
                    user_value=user_value,
                    is_enable=is_enable
                )
                session.add(new_config)
                logger.info(f"✅ 创建用户 '{user_name}' 的 {notify_method} 通知配置")
    
    def sync_devices(self, devices_data: List[Dict], group_name_to_id: Dict[str, int], session):
        """同步设备数据（增量更新）"""
        logger.info("开始同步设备数据...")
        
        for device_data in devices_data:
            device_name = device_data['device']
            location = device_data.get('location', '')
            is_effective = device_data.get('is_effective', True)
            device_type = device_data.get('device_type', '')
            address = device_data['address']
            port = device_data.get('port')
            check_method = device_data.get('check_method', 'icmp')
            notify_group = device_data.get('notify_group')
            
            # 获取组ID
            group_id = None
            if notify_group and notify_group in group_name_to_id:
                group_id = group_name_to_id[notify_group]
            
            # 检查设备是否已存在（根据名称和地址）
            existing_device = session.query(Devices).filter_by(
                name=device_name,
                address=address
            ).first()
            
            if existing_device:
                # 更新现有设备
                existing_device.location = location
                existing_device.is_enable = is_effective
                existing_device.device_type = device_type
                existing_device.port = port
                existing_device.check_method = check_method
                existing_device.group_id = group_id
                logger.info(f"✅ 更新设备: {device_name}")
            else:
                # 创建新设备
                new_device = Devices(
                    name=device_name,
                    location=location,
                    is_enable=is_effective,
                    device_type=device_type,
                    address=address,
                    port=port,
                    check_method=check_method,
                    group_id=group_id
                )
                session.add(new_device)
                logger.info(f"✅ 创建新设备: {device_name}")
    
    def sync_data(self):
        """同步所有数据"""
        try:
            # 加载配置数据
            data = self.load_yaml_data()
            
            with get_session() as session:
                # 1. 同步用户组
                groups_data = data.get('groups', [])
                group_name_to_id = self.sync_groups(groups_data, session)
                
                # 2. 同步用户
                users_data = data.get('users', [])
                user_name_to_id = self.sync_users(users_data, group_name_to_id, session)
                
                # 3. 同步用户通知配置
                notify_configs_data = data.get('user_notify_configurations', [])
                self.sync_user_notify_configs(notify_configs_data, user_name_to_id, session)
                
                # 4. 同步设备
                devices_data = data.get('devices', [])
                self.sync_devices(devices_data, group_name_to_id, session)
                
                logger.info("✅ 所有数据同步完成")
                
        except Exception as e:
            logger.error(f"❌ 数据同步失败: {e}")
            raise
    
    def get_stats(self):
        """获取数据库统计信息"""
        try:
            with get_session() as session:
                groups_count = session.query(Group).count()
                users_count = session.query(User).count()
                configs_count = session.query(UserNotifyConfig).count()
                devices_count = session.query(Devices).count()
                
                logger.info("数据库统计信息:")
                logger.info(f"  用户组: {groups_count}")
                logger.info(f"  用户: {users_count}")
                logger.info(f"  通知配置: {configs_count}")
                logger.info(f"  设备: {devices_count}")
                
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='数据库初始化脚本')
    parser.add_argument('--action', choices=['init', 'sync', 'rebuild', 'stats'], 
                       default='sync', help='执行的操作 (default: sync)')
    parser.add_argument('--yaml-file', default='datasource/source.yaml',
                       help='YAML配置文件路径 (default: datasource/source.yaml)')
    
    args = parser.parse_args()
    
    initializer = DatabaseInitializer(args.yaml_file)
    
    try:
        if args.action == 'init':
            logger.info("🚀 开始初始化数据库表结构...")
            initializer.create_tables()
            
        elif args.action == 'sync':
            logger.info("🚀 开始增量同步数据...")
            initializer.create_tables()  # 确保表存在
            initializer.sync_data()
            initializer.get_stats()
            
        elif args.action == 'rebuild':
            logger.info("🚀 开始重建数据库...")
            # 删除所有表
            Base.metadata.drop_all(bind=engine)
            logger.info("📦 已删除所有表")
            # 重新创建表并同步数据
            initializer.create_tables()
            initializer.sync_data()
            initializer.get_stats()
            
        elif args.action == 'stats':
            logger.info("📊 获取数据库统计信息...")
            initializer.get_stats()
            
        logger.info("🎉 操作完成！")
        
    except Exception as e:
        logger.error(f"💥 操作失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
