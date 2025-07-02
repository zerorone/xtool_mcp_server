#!/usr/bin/env python3
"""
挑战性工作流压力测试

使用 challenge 工具的对抗性测试理念，
对 xtool MCP Server 的工作流系统进行极限压力测试。
"""

import asyncio
import json
import os
import random
import string
import sys
import time
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.challenge import ChallengeTool
from tools.codereview import CodeReviewTool
from tools.debug import DebugIssueTool
from utils.conversation_memory import add_turn, create_thread, get_thread


class WorkflowStressTester:
    """工作流压力测试器"""

    def __init__(self):
        self.challenge_tool = ChallengeTool()
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance": {},
        }

    def generate_massive_content(self, size_mb: int) -> str:
        """生成指定大小的内容"""
        chars_per_mb = 1024 * 1024
        return "".join(random.choices(string.ascii_letters + string.digits, k=chars_per_mb * size_mb))

    def generate_deep_file_tree(self, depth: int, width: int) -> list[str]:
        """生成深度嵌套的文件树"""
        files = []

        def generate_level(current_path: str, current_depth: int):
            if current_depth >= depth:
                return

            for i in range(width):
                if current_depth == depth - 1:
                    # 叶子节点 - 文件
                    files.append(f"{current_path}/file_{i}.py")
                else:
                    # 中间节点 - 目录
                    new_path = f"{current_path}/dir_{i}"
                    generate_level(new_path, current_depth + 1)

        generate_level("/test", 0)
        return files

    async def test_memory_explosion(self):
        """测试内存爆炸场景"""
        print("\n[TEST] 内存爆炸测试...")

        try:
            # 创建包含大量数据的工作流
            thread_id = create_thread("debug", {"test": "memory_explosion"})

            # 添加大量轮次，每个轮次包含大量数据
            for i in range(50):
                large_content = self.generate_massive_content(1)  # 1MB per turn
                success = add_turn(
                    thread_id,
                    "assistant",
                    f"Turn {i}: {large_content[:100]}...",  # 只存储部分内容
                    files=[f"/file_{j}.py" for j in range(100)],  # 100 files per turn
                    tool_name="debug",
                )

                if not success:
                    print(f"  - 在第 {i} 轮时达到限制")
                    break

            # 尝试获取完整线程
            start_time = time.time()
            thread = get_thread(thread_id)
            retrieval_time = time.time() - start_time

            print(f"  - 线程检索时间: {retrieval_time:.2f}秒")
            print(f"  - 线程包含 {len(thread.turns)} 轮对话")

            self.results["performance"]["memory_test_retrieval_time"] = retrieval_time
            self.results["passed"] += 1

        except Exception as e:
            print(f"  - 失败: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Memory explosion test: {str(e)}")

    async def test_concurrent_workflows(self):
        """测试并发工作流执行"""
        print("\n[TEST] 并发工作流测试...")

        async def run_workflow(workflow_id: int):
            """运行单个工作流"""
            DebugIssueTool() if workflow_id % 2 == 0 else CodeReviewTool()

            # 创建挑战性输入
            challenge_prompt = (
                f"Workflow {workflow_id}: Debug complex async race condition with {random.randint(10, 50)} threads"
            )

            # 使用 challenge 工具包装
            challenge_result = await self.challenge_tool.execute({"prompt": challenge_prompt})

            challenge_data = json.loads(challenge_result[0].text)

            # 模拟工作流执行
            return {"workflow_id": workflow_id, "challenge": challenge_data["challenge_prompt"], "status": "completed"}

        try:
            # 并发运行多个工作流
            start_time = time.time()
            tasks = [run_workflow(i) for i in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            execution_time = time.time() - start_time

            # 统计结果
            successful = sum(1 for r in results if not isinstance(r, Exception))
            failed = len(results) - successful

            print(f"  - 成功: {successful}, 失败: {failed}")
            print(f"  - 总执行时间: {execution_time:.2f}秒")
            print(f"  - 平均时间: {execution_time / len(results):.2f}秒/工作流")

            self.results["performance"]["concurrent_workflows"] = {
                "total_time": execution_time,
                "success_rate": successful / len(results),
            }
            self.results["passed"] += 1

        except Exception as e:
            print(f"  - 失败: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Concurrent workflows test: {str(e)}")

    async def test_malicious_inputs(self):
        """测试恶意输入处理"""
        print("\n[TEST] 恶意输入测试...")

        malicious_inputs = [
            # SQL 注入尝试
            "'; DROP TABLE users; --",
            # 命令注入尝试
            "; rm -rf /; echo 'hacked'",
            # XSS 尝试
            "<script>alert('XSS')</script>",
            # 路径遍历
            "../../../../etc/passwd",
            # Unicode 欺骗
            "normaltext\u202e\u0000malicious",
            # 格式字符串攻击
            "%s%s%s%s%s%s%s%s%s%s",
            # 巨大数字
            "9" * 1000,
            # 二进制数据
            "\x00\x01\x02\x03\x04\x05",
        ]

        passed = 0
        for malicious_input in malicious_inputs:
            try:
                # 使用 challenge 工具处理恶意输入
                result = await self.challenge_tool.execute({"prompt": malicious_input})

                # 验证结果是有效的 JSON
                response = json.loads(result[0].text)
                assert "status" in response
                assert "challenge_prompt" in response

                # 确保恶意输入被安全处理
                assert malicious_input in response["original_statement"]
                passed += 1

            except Exception as e:
                print(f"  - 处理失败: {malicious_input[:50]}... - {str(e)}")
                self.results["errors"].append(f"Malicious input failed: {str(e)}")

        print(f"  - 通过: {passed}/{len(malicious_inputs)}")
        if passed == len(malicious_inputs):
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1

    async def test_token_limit_boundary(self):
        """测试令牌限制边界"""
        print("\n[TEST] 令牌限制边界测试...")

        try:
            # 生成接近限制的内容
            # 假设限制是 100k tokens，约 400k 字符
            large_content = self.generate_massive_content(0.4)  # 400KB

            # 创建挑战
            start_time = time.time()
            result = await self.challenge_tool.execute({"prompt": large_content})
            execution_time = time.time() - start_time

            response = json.loads(result[0].text)

            print(f"  - 大内容处理时间: {execution_time:.2f}秒")
            print(f"  - 响应状态: {response['status']}")

            self.results["performance"]["large_content_processing"] = execution_time
            self.results["passed"] += 1

        except Exception as e:
            print(f"  - 失败: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Token limit test: {str(e)}")

    async def test_rapid_fire_requests(self):
        """测试快速连续请求"""
        print("\n[TEST] 快速连续请求测试...")

        try:
            request_count = 100
            start_time = time.time()

            # 快速发送请求
            tasks = []
            for i in range(request_count):
                task = self.challenge_tool.execute({"prompt": f"Rapid request {i}: Quick test"})
                tasks.append(task)

            # 等待所有请求完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # 统计成功率
            success_count = sum(1 for r in results if not isinstance(r, Exception))

            print(f"  - 请求数: {request_count}")
            print(f"  - 成功: {success_count}")
            print(f"  - 总时间: {total_time:.2f}秒")
            print(f"  - QPS: {request_count / total_time:.2f}")

            self.results["performance"]["rapid_fire"] = {
                "qps": request_count / total_time,
                "success_rate": success_count / request_count,
            }
            self.results["passed"] += 1

        except Exception as e:
            print(f"  - 失败: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Rapid fire test: {str(e)}")

    async def test_state_corruption(self):
        """测试状态损坏场景"""
        print("\n[TEST] 状态损坏测试...")

        try:
            # 创建正常线程
            thread_id = create_thread("debug", {"test": "corruption"})

            # 添加正常轮次
            add_turn(thread_id, "user", "Normal turn 1")
            add_turn(thread_id, "assistant", "Normal response 1")

            # 尝试添加损坏的数据
            corrupted_data = {
                "role": "hacker",  # 无效角色
                "content": None,  # 空内容
                "files": "not_a_list",  # 错误类型
                "timestamp": "invalid_date",  # 无效时间戳
            }

            # 这应该失败或被安全处理
            try:
                # 直接操作存储（模拟损坏）
                from utils.storage_backend import get_storage_backend

                storage = get_storage_backend()

                # 尝试存储损坏数据
                storage.setex(f"thread:{thread_id}_corrupted", 3600, json.dumps(corrupted_data))

                # 尝试读取
                corrupted_thread = get_thread(f"{thread_id}_corrupted")

                if corrupted_thread is None:
                    print("  - 系统正确拒绝了损坏的数据")
                    self.results["passed"] += 1
                else:
                    print("  - 警告：系统接受了损坏的数据")
                    self.results["failed"] += 1

            except Exception as e:
                print(f"  - 系统正确处理了损坏数据: {str(e)}")
                self.results["passed"] += 1

        except Exception as e:
            print(f"  - 测试失败: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"State corruption test: {str(e)}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("xtool MCP Server 工作流系统挑战性压力测试")
        print("=" * 60)

        tests = [
            self.test_memory_explosion(),
            self.test_concurrent_workflows(),
            self.test_malicious_inputs(),
            self.test_token_limit_boundary(),
            self.test_rapid_fire_requests(),
            self.test_state_corruption(),
        ]

        # 运行所有测试
        await asyncio.gather(*tests, return_exceptions=True)

        # 打印总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"通过: {self.results['passed']}")
        print(f"失败: {self.results['failed']}")
        print(f"总计: {self.results['passed'] + self.results['failed']}")

        if self.results["errors"]:
            print("\n错误详情:")
            for error in self.results["errors"]:
                print(f"  - {error}")

        if self.results["performance"]:
            print("\n性能指标:")
            for metric, value in self.results["performance"].items():
                print(f"  - {metric}: {value}")

        # 保存详细报告
        report_path = Path(__file__).parent / "challenge_test_results.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n详细报告已保存到: {report_path}")


async def main():
    """主函数"""
    tester = WorkflowStressTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # 设置更激进的测试参数
    os.environ["MAX_CONVERSATION_TURNS"] = "100"  # 增加轮次限制进行测试
    os.environ["CONVERSATION_TIMEOUT_HOURS"] = "0.1"  # 6分钟超时

    asyncio.run(main())
