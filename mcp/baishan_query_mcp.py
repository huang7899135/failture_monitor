#!/usr/bin/env python3
"""
白山故障监控 MCP 服务器

该服务器提供以下功能：
1. 查询故障账号
2. 查询故障服务器
3. 查询故障节点
4. 执行账号拨号
5. 执行压测
6. 查询服务器压测结果
7. 自动恢复账号和服务器
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目模块
from fastmcp import FastMCP


def get_baishan_client(supplier: str):
    """动态导入并创建 Baishan 客户端"""
    try:
        from checker.webpage_checker.sites.baishan import Baishan
        return Baishan(supplier)
    except ImportError as e:
        raise ImportError(f"无法导入 Baishan 模块: {e}")


# 创建 MCP 服务器实例
mcp = FastMCP("白山故障监控")


def format_response(success: bool, data: Any = None, message: str = "") -> Dict[str, Any]:
    """格式化响应"""
    return {
        "success": success,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def handle_baishan_error(func):
    """装饰器：处理白山操作的错误"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return format_response(False, None, f"操作失败: {str(e)}")
    return wrapper


@mcp.tool()
@handle_baishan_error
def query_fault_accounts(supplier: str = "yicheng") -> Dict[str, Any]:
    """
    查询故障账号
    
    Args:
        supplier: 供应商名称，可选 "yicheng" 或 "vision_blue"
    
    Returns:
        包含故障账号列表的字典
    """
    with get_baishan_client(supplier) as client:
        result = client.query_faulty_accounts()
        
        # 统计信息
        accounts = result.get('account_fault_list', [])
        stats = {
            "total_count": result.get('total_count', 0),
            "current_page": result.get('current_page', 1),
            "page_count": result.get('page_count', 1),
            "per_page": result.get('per_page', 0),
            "fault_accounts_count": len(accounts)
        }
        
        # 按状态分类账号
        status_summary = {}
        for account in accounts:
            dial_status = account.get('dial_status', 'unknown')
            pressure_status = account.get('pressure_test_status', 'unknown')
            key = f"dial_{dial_status}_pressure_{pressure_status}"
            status_summary[key] = status_summary.get(key, 0) + 1
        
        return format_response(True, {
            "statistics": stats,
            "status_summary": status_summary,
            "accounts": accounts[:10],  # 只返回前10个账号的详细信息
            "full_data_available": len(accounts)
        }, f"成功查询到 {len(accounts)} 个故障账号")


@mcp.tool()
@handle_baishan_error
def query_fault_servers(supplier: str = "yicheng") -> Dict[str, Any]:
    """
    查询故障服务器
    
    Args:
        supplier: 供应商名称，可选 "yicheng" 或 "vision_blue"
    
    Returns:
        包含故障服务器列表的字典
    """
    with get_baishan_client(supplier) as client:
        servers = client.query_faulty_servers()
        
        # 统计信息
        status_summary = {}
        for server in servers:
            status = server.get('status', 'unknown')
            check_status = server.get('check_status', 'unknown')
            key = f"status_{status}_check_{check_status}"
            status_summary[key] = status_summary.get(key, 0) + 1
        
        return format_response(True, {
            "total_servers": len(servers),
            "status_summary": status_summary,
            "servers": servers[:10],  # 只返回前10个服务器的详细信息
            "full_data_available": len(servers)
        }, f"成功查询到 {len(servers)} 个故障服务器")


@mcp.tool()
@handle_baishan_error
def get_system_status(supplier: str = "yicheng") -> Dict[str, Any]:
    """
    获取白山系统整体状态概览
    
    Args:
        supplier: 供应商名称，可选 "yicheng" 或 "vision_blue"
    
    Returns:
        系统状态概览
    """
    with get_baishan_client(supplier) as client:
        # 查询各类故障数据
        accounts = client.query_faulty_accounts()
        servers = client.query_faulty_servers()
        nodes = client.query_faulty_nodes()
        
        return format_response(True, {
            "supplier": supplier,
            "fault_summary": {
                "accounts": {
                    "total": accounts.get('total_count', 0),
                    "current_page_count": len(accounts.get('account_fault_list', []))
                },
                "servers": {
                    "total": len(servers)
                },
                "nodes": {
                    "total": len(nodes)
                }
            },
            "query_time": datetime.now().isoformat()
        }, f"{supplier} 系统状态查询完成")


@mcp.tool()
def get_available_suppliers() -> Dict[str, Any]:
    """
    获取可用的供应商列表
    
    Returns:
        可用供应商的信息
    """
    return format_response(True, {
        "suppliers": [
            {
                "id": "yicheng",
                "name": "宜成",
                "description": "宜成供应商"
            },
            {
                "id": "vision_blue", 
                "name": "视觉蓝",
                "description": "视觉蓝供应商"
            }
        ],
        "default": "yicheng"
    }, "成功获取供应商列表")


@mcp.tool()
def get_help() -> Dict[str, Any]:
    """
    获取帮助信息
    
    Returns:
        MCP服务器的使用说明
    """
    help_info = {
        "description": "白山故障监控 MCP 服务器",
        "version": "1.0.0",
        "available_tools": [
            {
                "name": "query_fault_accounts",
                "description": "查询故障账号",
                "parameters": ["supplier (可选)"]
            },
            {
                "name": "query_fault_servers", 
                "description": "查询故障服务器",
                "parameters": ["supplier (可选)"]
            },
            {
                "name": "get_system_status",
                "description": "获取系统状态概览",
                "parameters": ["supplier (可选)"]
            },
            {
                "name": "get_available_suppliers",
                "description": "获取可用供应商列表",
                "parameters": []
            }
        ],
        "suppliers": ["yicheng", "vision_blue"],
        "usage_examples": [
            "query_fault_accounts(supplier='yicheng')",
            "query_fault_servers(supplier='vision_blue')",
            "get_system_status(supplier='yicheng')"
        ]
    }
    
    return format_response(True, help_info, "帮助信息获取成功")


def main():
    """启动 MCP 服务器"""
    # 设置环境变量
    if 'APP_ENV' not in os.environ:
        os.environ['APP_ENV'] = 'dev'
    
    print("🚀 启动白山故障监控 MCP 服务器...")
    print("📋 可用工具:")
    print("   - query_fault_accounts: 查询故障账号")
    print("   - query_fault_servers: 查询故障服务器") 
    print("   - get_system_status: 获取系统状态概览")
    print("   - get_available_suppliers: 获取可用供应商")
    print("   - get_help: 获取帮助信息")
    print("🏢 支持供应商: yicheng, vision_blue")
    print()
    
    # 启动服务器
    mcp.run()


if __name__ == "__main__":
    main()
        