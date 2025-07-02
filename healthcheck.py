#!/usr/bin/env python3
"""
简单的健康检查脚本
Simple health check script for XTool MCP Server
"""

import sys
import os

def main():
    """简单的健康检查"""
    try:
        # 检查核心模块是否可以导入
        import server
        import config
        
        # 检查基本文件是否存在
        required_files = ['server.py', 'config.py']
        for file in required_files:
            if not os.path.exists(f'/app/{file}'):
                print(f"❌ 缺少必需文件: {file}")
                sys.exit(1)
        
        print("✅ 健康检查通过")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()