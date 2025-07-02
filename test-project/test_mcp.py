#!/usr/bin/env python3
"""
测试MCP服务功能的简单Python脚本
"""

def add(a, b):
    """
    简单的加法函数
    """
    return a + b

def multiply(a, b):
    """
    简单的乘法函数
    """
    return a * b

def divide(a, b):
    """
    除法函数，包含错误处理
    """
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

class Calculator:
    """
    简单的计算器类
    """
    def __init__(self):
        self.history = []
    
    def calculate(self, operation, a, b):
        """
        执行计算并记录历史
        """
        if operation == "add":
            result = add(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        elif operation == "divide":
            result = divide(a, b)
        else:
            raise ValueError(f"未知的操作: {operation}")
        
        self.history.append({
            "operation": operation,
            "a": a,
            "b": b,
            "result": result
        })
        return result
    
    def get_history(self):
        """
        获取计算历史
        """
        return self.history

if __name__ == "__main__":
    # 测试代码
    calc = Calculator()
    print("加法测试:", calc.calculate("add", 10, 5))
    print("乘法测试:", calc.calculate("multiply", 10, 5))
    print("除法测试:", calc.calculate("divide", 10, 5))
    
    print("\n计算历史:")
    for record in calc.get_history():
        print(f"  {record['a']} {record['operation']} {record['b']} = {record['result']}")