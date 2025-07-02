"""
Performance and Stress Test Suite for Zen MCP Server

This test suite evaluates the performance characteristics and stress handling
capabilities of the MCP server under various load conditions.
"""

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from server import handle_call_tool, handle_list_tools
from utils.path_intelligence import PathIntelligence
from utils.project_detector import ProjectDetector
from utils.todo_parser import TodoParser


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test run"""

    operation: str
    total_time: float
    average_time: float
    min_time: float
    max_time: float
    percentile_95: float
    throughput: float
    success_rate: float


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time


class TestToolPerformance:
    """Test performance of individual tools"""

    @pytest.mark.asyncio
    async def test_tool_discovery_performance(self):
        """Test tool discovery performance"""
        timings = []

        # Warm up
        await handle_list_tools()

        # Measure
        for _ in range(100):
            with PerformanceTimer() as timer:
                tools = await handle_list_tools()
            timings.append(timer.duration)

        metrics = self._calculate_metrics("tool_discovery", timings, 100)

        # Assertions
        assert metrics.average_time < 0.001  # Should be under 1ms
        assert metrics.percentile_95 < 0.002  # 95% under 2ms
        assert len(tools) > 15  # Should have all tools

        self._print_metrics(metrics)

    @pytest.mark.asyncio
    async def test_thinkboost_performance(self):
        """Test thinkboost tool performance (no AI calls)"""
        timings = []

        # Test various input sizes
        test_cases = [
            {"problem": "Short problem", "context": ""},
            {"problem": "Medium problem " * 10, "context": "Some context " * 5},
            {"problem": "Large problem " * 50, "context": "Large context " * 50},
        ]

        for args in test_cases * 10:  # 30 total calls
            with PerformanceTimer() as timer:
                result = await handle_call_tool("thinkboost", args)

            if result.status == "success":
                timings.append(timer.duration)

        metrics = self._calculate_metrics("thinkboost", timings, len(test_cases) * 10)

        # Assertions
        assert metrics.average_time < 0.01  # Should be under 10ms
        assert metrics.percentile_95 < 0.02  # 95% under 20ms
        assert metrics.success_rate == 1.0  # All should succeed

        self._print_metrics(metrics)

    @pytest.mark.asyncio
    async def test_memory_operations_performance(self):
        """Test memory tool performance"""
        save_timings = []
        recall_timings = []

        # Test save operations
        for i in range(50):
            content = f"Test content {i} " * 10
            args = {"operation": "save", "content": content, "metadata": {"index": i, "test": True}}

            with PerformanceTimer() as timer:
                result = await handle_call_tool("memory", args)

            if result.status == "success":
                save_timings.append(timer.duration)

        # Test recall operations
        for i in range(50):
            args = {"operation": "recall", "query": f"Test content {i}"}

            with PerformanceTimer() as timer:
                result = await handle_call_tool("memory", args)

            if result.status == "success":
                recall_timings.append(timer.duration)

        save_metrics = self._calculate_metrics("memory_save", save_timings, 50)
        recall_metrics = self._calculate_metrics("memory_recall", recall_timings, 50)

        # Assertions
        assert save_metrics.average_time < 0.05  # Save under 50ms
        assert recall_metrics.average_time < 0.05  # Recall under 50ms

        self._print_metrics(save_metrics)
        self._print_metrics(recall_metrics)

    def _calculate_metrics(self, operation: str, timings: list[float], total_ops: int) -> PerformanceMetrics:
        """Calculate performance metrics from timings"""
        if not timings:
            return PerformanceMetrics(
                operation=operation,
                total_time=0,
                average_time=0,
                min_time=0,
                max_time=0,
                percentile_95=0,
                throughput=0,
                success_rate=0,
            )

        sorted_timings = sorted(timings)
        total_time = sum(timings)

        return PerformanceMetrics(
            operation=operation,
            total_time=total_time,
            average_time=total_time / len(timings),
            min_time=sorted_timings[0],
            max_time=sorted_timings[-1],
            percentile_95=sorted_timings[int(len(sorted_timings) * 0.95)],
            throughput=len(timings) / total_time if total_time > 0 else 0,
            success_rate=len(timings) / total_ops,
        )

    def _print_metrics(self, metrics: PerformanceMetrics):
        """Print performance metrics"""
        print(f"\n{metrics.operation} Performance Metrics:")
        print(f"  Average: {metrics.average_time * 1000:.2f}ms")
        print(f"  Min: {metrics.min_time * 1000:.2f}ms")
        print(f"  Max: {metrics.max_time * 1000:.2f}ms")
        print(f"  95th percentile: {metrics.percentile_95 * 1000:.2f}ms")
        print(f"  Throughput: {metrics.throughput:.2f} ops/sec")
        print(f"  Success rate: {metrics.success_rate * 100:.1f}%")


class TestConcurrentLoad:
    """Test server behavior under concurrent load"""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test handling multiple concurrent tool calls"""

        async def make_tool_call(tool_name: str, args: dict):
            try:
                result = await handle_call_tool(tool_name, args)
                return result.status == "success"
            except Exception:
                return False

        # Create diverse workload
        tasks = []

        # Mix of different tools
        for i in range(20):
            tasks.append(make_tool_call("version", {}))
            tasks.append(make_tool_call("thinkboost", {"problem": f"Problem {i}", "context": "Concurrent test"}))
            tasks.append(
                make_tool_call(
                    "memory", {"operation": "save", "content": f"Concurrent test {i}", "metadata": {"test": i}}
                )
            )

        # Execute all concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()

        # Calculate metrics
        successful = sum(1 for r in results if r is True)
        total_time = end_time - start_time

        print("\nConcurrent Load Test:")
        print(f"  Total operations: {len(tasks)}")
        print(f"  Successful: {successful}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {len(tasks) / total_time:.2f} ops/sec")

        # Assertions
        assert successful >= len(tasks) * 0.95  # At least 95% success rate
        assert total_time < 10  # Should complete within 10 seconds

    @pytest.mark.asyncio
    async def test_memory_concurrent_access(self):
        """Test concurrent memory access patterns"""

        async def memory_operation(op_type: str, key: str, value: str = None):
            if op_type == "save":
                args = {"operation": "save", "content": value, "metadata": {"key": key}}
            else:  # recall
                args = {"operation": "recall", "query": key}

            try:
                result = await handle_call_tool("memory", args)
                return result.status == "success"
            except Exception:
                return False

        # Create interleaved read/write operations
        tasks = []
        for i in range(50):
            # Write
            tasks.append(memory_operation("save", f"key_{i}", f"value_{i}"))
            # Read same key
            tasks.append(memory_operation("recall", f"key_{i}"))
            # Read different key
            if i > 0:
                tasks.append(memory_operation("recall", f"key_{i - 1}"))

        # Execute
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()

        successful = sum(1 for r in results if r is True)

        print("\nMemory Concurrent Access Test:")
        print(f"  Operations: {len(tasks)}")
        print(f"  Successful: {successful}")
        print(f"  Time: {end_time - start_time:.2f}s")

        assert successful >= len(tasks) * 0.9  # 90% success rate


class TestMemoryPressure:
    """Test server behavior under memory pressure"""

    @pytest.mark.asyncio
    async def test_large_memory_storage(self):
        """Test handling of large memory storage"""
        large_content_sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
        timings = {}

        for size in large_content_sizes:
            content = "x" * size
            timing_list = []

            for i in range(10):
                args = {"operation": "save", "content": content, "metadata": {"size": size, "index": i}}

                with PerformanceTimer() as timer:
                    result = await handle_call_tool("memory", args)

                if result.status == "success":
                    timing_list.append(timer.duration)

            timings[size] = timing_list

        # Print results
        print("\nLarge Memory Storage Test:")
        for size, times in timings.items():
            avg_time = sum(times) / len(times) if times else 0
            print(f"  {size / 1024:.0f}KB: {avg_time * 1000:.2f}ms average")

        # Assertions - larger content should still be reasonably fast
        for size, times in timings.items():
            avg_time = sum(times) / len(times) if times else 0
            assert avg_time < 0.1  # Under 100ms even for large content

    @pytest.mark.asyncio
    async def test_memory_accumulation(self):
        """Test behavior with accumulated memory entries"""
        # Save many entries
        for i in range(100):
            args = {
                "operation": "save",
                "content": f"Entry {i} with some content to make it realistic",
                "metadata": {"index": i, "category": i % 10},
            }
            await handle_call_tool("memory", args)

        # Test recall performance with many entries
        recall_times = []

        for i in range(20):
            args = {"operation": "recall", "query": f"Entry {i}"}

            with PerformanceTimer() as timer:
                result = await handle_call_tool("memory", args)

            if result.status == "success":
                recall_times.append(timer.duration)

        avg_recall_time = sum(recall_times) / len(recall_times)

        print("\nMemory Accumulation Test:")
        print("  Stored entries: 100")
        print(f"  Avg recall time: {avg_recall_time * 1000:.2f}ms")

        assert avg_recall_time < 0.05  # Under 50ms average


class TestUtilityPerformance:
    """Test performance of utility modules"""

    def test_todo_parser_performance(self):
        """Test TODO parser performance"""
        # Create a large TODO content
        todo_content = """
# Large Project TODO

## Phase 1: Foundation
"""

        # Add many tasks
        for i in range(100):
            todo_content += f"- [ ] Task {i} description [{'!' * (i % 3 + 1)}] ({i % 8 + 1}h) #tag{i % 5}\n"
            if i % 10 == 0:
                for j in range(3):
                    todo_content += f"  - [ ] Subtask {i}.{j} #subtag\n"

        # Add dependencies
        todo_content += "\n## Dependencies\n"
        for i in range(20):
            todo_content += f'- Task "Task {i + 10}" requires "Task {i}"\n'

        # Measure parsing performance
        parser = TodoParser()

        with PerformanceTimer() as timer:
            tasks = parser.parse_content(todo_content)

        print("\nTODO Parser Performance:")
        print(f"  Tasks parsed: {len(tasks)}")
        print(f"  Parse time: {timer.duration * 1000:.2f}ms")
        print(f"  Tasks/sec: {len(tasks) / timer.duration:.0f}")

        assert timer.duration < 0.1  # Should parse in under 100ms
        assert len(tasks) > 100  # Should have parsed all tasks

    def test_project_detector_performance(self):
        """Test project detector performance"""
        detector = ProjectDetector()

        # Test on current directory
        with PerformanceTimer() as timer:
            env = detector.detect_project(".")

        print("\nProject Detector Performance:")
        print(f"  Detection time: {timer.duration * 1000:.2f}ms")
        print(f"  Project type: {env.project_type.value}")
        print(f"  Files analyzed: {env.structure['total_files']}")

        assert timer.duration < 1.0  # Should complete in under 1 second

    def test_path_intelligence_performance(self):
        """Test path intelligence performance"""
        path_intel = PathIntelligence()

        # Learn some patterns
        for i in range(50):
            path_intel.learn_path_usage(
                f"src/module_{i % 5}/file_{i}.py", path_intel._infer_path_type(f"file_{i}.py"), f"context_{i % 3}"
            )

        # Test recommendation performance
        recommendation_times = []

        for partial in ["src/", "test", "file_", "module"]:
            with PerformanceTimer() as timer:
                path_intel.recommend_paths(partial)
            recommendation_times.append(timer.duration)

        avg_time = sum(recommendation_times) / len(recommendation_times)

        print("\nPath Intelligence Performance:")
        print("  Learned patterns: 50")
        print(f"  Avg recommendation time: {avg_time * 1000:.2f}ms")

        assert avg_time < 0.01  # Under 10ms average


class TestStressScenarios:
    """Test extreme stress scenarios"""

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self):
        """Test handling rapid sequential requests"""
        request_count = 200
        success_count = 0

        start_time = time.perf_counter()

        for i in range(request_count):
            try:
                # Alternate between different tools
                if i % 3 == 0:
                    result = await handle_call_tool("version", {})
                elif i % 3 == 1:
                    result = await handle_call_tool("thinkboost", {"problem": f"Rapid test {i}", "context": ""})
                else:
                    result = await handle_call_tool(
                        "memory", {"operation": "save", "content": f"Rapid {i}", "metadata": {"i": i}}
                    )

                if result.status == "success":
                    success_count += 1
            except Exception:
                pass

        end_time = time.perf_counter()
        total_time = end_time - start_time

        print("\nRapid Fire Test:")
        print(f"  Requests: {request_count}")
        print(f"  Successful: {success_count}")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Rate: {request_count / total_time:.0f} req/sec")

        assert success_count >= request_count * 0.95  # 95% success
        assert request_count / total_time > 50  # At least 50 req/sec

    @pytest.mark.asyncio
    async def test_mixed_workload_stress(self):
        """Test mixed workload under stress"""

        # Create a mixed workload
        async def workload_task(task_id: int):
            operations = []

            # Each task does multiple operations
            for i in range(5):
                op_type = (task_id + i) % 4

                if op_type == 0:
                    # Tool discovery
                    operations.append(handle_list_tools())
                elif op_type == 1:
                    # ThinkBoost
                    operations.append(
                        handle_call_tool(
                            "thinkboost", {"problem": f"Task {task_id} problem {i}", "context": "Stress test"}
                        )
                    )
                elif op_type == 2:
                    # Memory save
                    operations.append(
                        handle_call_tool(
                            "memory",
                            {"operation": "save", "content": f"Task {task_id} data {i}", "metadata": {"task": task_id}},
                        )
                    )
                else:
                    # Memory recall
                    operations.append(handle_call_tool("memory", {"operation": "recall", "query": f"Task {task_id}"}))

            results = await asyncio.gather(*operations, return_exceptions=True)
            return sum(1 for r in results if not isinstance(r, Exception))

        # Run multiple workload tasks concurrently
        start_time = time.perf_counter()

        workload_tasks = [workload_task(i) for i in range(20)]
        results = await asyncio.gather(*workload_tasks)

        end_time = time.perf_counter()

        total_ops = sum(results)
        total_possible = 20 * 5  # 20 tasks * 5 ops each

        print("\nMixed Workload Stress Test:")
        print(f"  Total operations: {total_possible}")
        print(f"  Successful: {total_ops}")
        print(f"  Success rate: {total_ops / total_possible * 100:.1f}%")
        print(f"  Time: {end_time - start_time:.2f}s")

        assert total_ops >= total_possible * 0.9  # 90% success rate


def run_performance_suite():
    """Run the complete performance test suite"""
    print("=" * 60)
    print("Zen MCP Server Performance Test Suite")
    print("=" * 60)

    # Run all performance tests
    pytest.main([__file__, "-v", "-s", "-k", "test_"])


if __name__ == "__main__":
    run_performance_suite()
