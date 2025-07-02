#!/usr/bin/env python3
"""
增强版健康检查脚本 - 支持文件处理优化和监控功能检查
"""

import json
import os
import subprocess
import sys
import time


def check_process():
    """检查主服务器进程是否运行"""
    try:
        result = subprocess.run(["pgrep", "-f", "server.py"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, "服务器进程正常运行"
        return False, f"进程检查失败: {result.stderr}"
    except Exception as e:
        return False, f"进程检查异常: {e}"


def check_python_imports():
    """检查关键 Python 模块是否可以导入"""
    critical_modules = [
        "mcp",
        "google.genai",
        "openai",
        "pydantic",
        "dotenv",
        # 增强功能相关模块
        "asyncio",
        "threading",
        "hashlib",
        "sqlite3",
    ]

    failed_modules = []
    for module in critical_modules:
        try:
            __import__(module)
        except ImportError as e:
            failed_modules.append(f"{module}: {e}")
        except Exception as e:
            failed_modules.append(f"{module}: 意外错误 {e}")

    if failed_modules:
        return False, f"模块导入失败: {', '.join(failed_modules)}"
    return True, f"所有 {len(critical_modules)} 个关键模块导入成功"


def check_directories():
    """检查关键目录是否存在且可写"""
    directories = [
        "/app/logs",
        "/app/.zen_memory",
        "/app/.zen_memory/file_cache",
        "/app/.zen_memory/workflow_states",
        "/app/tmp",
    ]

    failed_dirs = []
    for dir_path in directories:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            # 测试写权限
            test_file = os.path.join(dir_path, ".health_check")
            with open(test_file, "w") as f:
                f.write("health_check")
            os.remove(test_file)

        except Exception as e:
            failed_dirs.append(f"{dir_path}: {e}")

    if failed_dirs:
        return False, f"目录检查失败: {', '.join(failed_dirs)}"
    return True, f"所有 {len(directories)} 个目录可访问"


def check_environment():
    """检查环境变量配置"""
    # API 密钥检查
    api_keys = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "XAI_API_KEY",
        "DIAL_API_KEY",
        "OPENROUTER_API_KEY",
        "CUSTOM_API_KEY",
    ]

    valid_keys = []
    for key in api_keys:
        value = os.getenv(key)
        if value and len(value.strip()) >= 10:
            valid_keys.append(key)

    if not valid_keys:
        return False, "未找到有效的 API 密钥"

    # 检查优化功能配置
    optimization_enabled = os.getenv("ZEN_FILE_OPTIMIZATION_ENABLED", "true").lower() == "true"
    persistence_enabled = os.getenv("ZEN_WORKFLOW_PERSISTENCE_ENABLED", "true").lower() == "true"

    config_info = {
        "api_keys_count": len(valid_keys),
        "file_optimization": optimization_enabled,
        "workflow_persistence": persistence_enabled,
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }

    return True, f"环境配置正常: {json.dumps(config_info)}"


def check_enhanced_features():
    """检查增强功能是否可用"""
    try:
        # 测试文件处理优化
        sys.path.append("/app")
        from utils.enhanced_file_processor import get_enhanced_file_processor
        from utils.file_processing_integration import get_file_processing_integration
        from utils.workflow_memory_fix import get_workflow_manager

        # 初始化组件
        processor = get_enhanced_file_processor()
        integration = get_file_processing_integration()
        workflow_manager = get_workflow_manager()

        # 获取状态
        cache_stats = processor.get_cache_stats()
        workflow_stats = workflow_manager.get_global_stats()

        status = {
            "file_processor": "可用",
            "cache_items": cache_stats["cache_stats"]["memory_cache"]["items"]
            + cache_stats["cache_stats"]["disk_cache"]["items"],
            "workflow_manager": "可用",
            "active_workflows": workflow_stats["active_workflows"],
            "persistence_enabled": workflow_stats.get("persistence_enabled", False),
        }

        return True, f"增强功能检查通过: {json.dumps(status)}"

    except Exception as e:
        return False, f"增强功能检查失败: {e}"


def check_monitoring_endpoints():
    """检查监控端点是否可用"""
    try:
        sys.path.append("/app")
        from tools.file_optimization_monitor import FileOptimizationMonitorTool
        from tools.workflow_monitor import WorkflowMonitorTool

        # 实例化监控工具
        workflow_monitor = WorkflowMonitorTool()
        file_monitor = FileOptimizationMonitorTool()

        # 验证工具名称
        assert workflow_monitor.get_name() == "workflow_monitor"
        assert file_monitor.get_name() == "file_optimization_monitor"

        return True, "监控端点可用"

    except Exception as e:
        return False, f"监控端点检查失败: {e}"


def check_storage_backends():
    """检查存储后端是否正常"""
    try:
        # 检查 SQLite 数据库
        db_path = "/app/.zen_memory/workflow_states.db"
        if os.path.exists(db_path):
            import sqlite3

            conn = sqlite3.connect(db_path, timeout=5.0)
            cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()

            return True, f"SQLite 后端正常，包含 {table_count} 个表"
        else:
            return True, "SQLite 后端将在首次使用时初始化"

    except Exception as e:
        return False, f"存储后端检查失败: {e}"


def main():
    """主健康检查函数"""
    # 检查是否为增强模式
    enhanced_mode = "--enhanced" in sys.argv

    # 基础检查
    basic_checks = [
        ("进程状态", check_process),
        ("Python 模块", check_python_imports),
        ("目录权限", check_directories),
        ("环境配置", check_environment),
    ]

    # 增强检查
    enhanced_checks = [
        ("增强功能", check_enhanced_features),
        ("监控端点", check_monitoring_endpoints),
        ("存储后端", check_storage_backends),
    ]

    all_checks = basic_checks + (enhanced_checks if enhanced_mode else [])

    results = []
    failed_checks = []

    print(f"🏥 开始健康检查 ({'增强模式' if enhanced_mode else '基础模式'})")
    print("=" * 60)

    for check_name, check_func in all_checks:
        try:
            start_time = time.time()
            success, message = check_func()
            duration = time.time() - start_time

            status = "✅ 通过" if success else "❌ 失败"
            print(f"{status} {check_name}: {message} ({duration:.3f}s)")

            results.append({"name": check_name, "success": success, "message": message, "duration": duration})

            if not success:
                failed_checks.append(check_name)

        except Exception as e:
            print(f"❌ {check_name}: 检查异常 - {e}")
            failed_checks.append(check_name)
            results.append({"name": check_name, "success": False, "message": f"检查异常: {e}", "duration": 0})

    print("=" * 60)

    # 生成总结
    total_checks = len(all_checks)
    passed_checks = total_checks - len(failed_checks)
    success_rate = (passed_checks / total_checks) * 100

    print(f"📊 检查结果: {passed_checks}/{total_checks} 通过 ({success_rate:.1f}%)")

    if failed_checks:
        print(f"❌ 失败的检查: {', '.join(failed_checks)}")

        # 写入详细日志
        try:
            log_path = "/app/logs/health_check.json"
            with open(log_path, "w") as f:
                json.dump(
                    {
                        "timestamp": time.time(),
                        "enhanced_mode": enhanced_mode,
                        "success_rate": success_rate,
                        "failed_checks": failed_checks,
                        "results": results,
                    },
                    f,
                    indent=2,
                )
            print(f"📝 详细日志已保存到: {log_path}")
        except Exception as e:
            print(f"⚠️  无法保存日志: {e}")

        sys.exit(1)
    else:
        print("🎉 所有健康检查通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
