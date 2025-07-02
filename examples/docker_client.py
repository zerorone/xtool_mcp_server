#!/usr/bin/env python3
"""
Zen MCP Server Docker 客户端示例
演示如何从其他项目调用运行在 Docker 中的 Zen MCP Server
"""

import json
import subprocess
from typing import Any, Dict, Optional


class ZenMCPDockerClient:
    """Docker 中的 Zen MCP Server 客户端"""

    def __init__(self, container_name: str = "zen-mcp-production"):
        self.container_name = container_name

    def _execute_in_container(self, python_code: str) -> str:
        """在容器中执行 Python 代码"""
        cmd = ["docker", "exec", self.container_name, "python", "-c", python_code]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise Exception(f"容器执行失败: {result.stderr}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise Exception("容器执行超时")
        except Exception as e:
            raise Exception(f"容器调用失败: {str(e)}")

    def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """调用指定的工具"""

        # 构建调用代码
        python_code = f"""
import json
import sys
import os
import asyncio

# 设置路径
sys.path.insert(0, '/app')
os.chdir('/app')

async def main():
    try:
        # 动态导入工具
        if "{tool_name}" == "chat":
            from tools.chat import ChatTool
            tool = ChatTool()
        elif "{tool_name}" == "thinkdeep":
            from tools.thinkdeep import ThinkDeepTool
            tool = ThinkDeepTool()
        elif "{tool_name}" == "memory":
            from tools.memory_manager import MemoryManagerTool
            tool = MemoryManagerTool()
        elif "{tool_name}" == "recall":
            from tools.memory_recall import MemoryRecallTool
            tool = MemoryRecallTool()
        elif "{tool_name}" == "listmodels":
            from tools.listmodels import ListModelsTool
            tool = ListModelsTool()
        elif "{tool_name}" == "version":
            from tools.version import VersionTool
            tool = VersionTool()
        else:
            raise ValueError(f"不支持的工具: {tool_name}")
        
        # 准备参数
        params = {json.dumps(kwargs, ensure_ascii=False)}
        
        # 执行工具
        if hasattr(tool, 'run'):
            if asyncio.iscoroutinefunction(tool.run):
                result = await tool.run(**params)
            else:
                result = tool.run(**params)
        else:
            raise ValueError(f"工具 {tool_name} 没有 run 方法")
        
        # 返回结果
        output = {{
            "success": True,
            "tool": "{tool_name}",
            "result": result,
            "params": params
        }}
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_output = {{
            "success": False,
            "tool": "{tool_name}",
            "error": str(e),
            "params": {json.dumps(kwargs, ensure_ascii=False)}
        }}
        print(json.dumps(error_output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
"""

        # 执行并解析结果
        output = self._execute_in_container(python_code)

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"success": False, "error": f"无法解析输出: {output}", "raw_output": output}

    def chat(self, prompt: str, files: Optional[list] = None, images: Optional[list] = None) -> Dict[str, Any]:
        """聊天工具"""
        return self.call_tool("chat", prompt=prompt, files=files or [], images=images or [])

    def list_models(self) -> Dict[str, Any]:
        """列出可用模型"""
        return self.call_tool("listmodels")

    def get_version(self) -> Dict[str, Any]:
        """获取版本信息"""
        return self.call_tool("version")

    def memory_save(self, content: str, layer: str = "session", **kwargs) -> Dict[str, Any]:
        """保存记忆"""
        return self.call_tool("memory", action="save", content=content, layer=layer, **kwargs)

    def memory_recall(self, query: str = None, **kwargs) -> Dict[str, Any]:
        """回忆记忆"""
        return self.call_tool("recall", query=query, **kwargs)

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            result = subprocess.run(
                ["docker", "exec", self.container_name, "python", "/usr/local/bin/healthcheck.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {"healthy": result.returncode == 0, "output": result.stdout, "error": result.stderr}
        except Exception as e:
            return {"healthy": False, "error": str(e)}


def main():
    """示例用法"""
    print("🚀 Zen MCP Server Docker 客户端示例")
    print("=" * 50)

    # 创建客户端
    client = ZenMCPDockerClient()

    # 健康检查
    print("\\n1. 健康检查:")
    health = client.health_check()
    print(f"健康状态: {'✅ 健康' if health['healthy'] else '❌ 不健康'}")

    # 获取版本信息
    print("\\n2. 版本信息:")
    version = client.get_version()
    if version.get("success"):
        print(f"版本: {version['result']}")
    else:
        print(f"获取版本失败: {version.get('error')}")

    # 列出模型
    print("\\n3. 可用模型:")
    models = client.list_models()
    if models.get("success"):
        print(f"模型数量: {len(models['result'])} 个")
    else:
        print(f"获取模型失败: {models.get('error')}")

    # 聊天示例
    print("\\n4. 聊天示例:")
    chat_result = client.chat("你好！请简单介绍一下 Zen MCP Server 的主要功能。")
    if chat_result.get("success"):
        print(f"回复: {chat_result['result'][:100]}...")
    else:
        print(f"聊天失败: {chat_result.get('error')}")

    print("\\n" + "=" * 50)
    print("✅ 示例完成！")


if __name__ == "__main__":
    main()
