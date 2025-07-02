#!/usr/bin/env python3
"""
交互式CLI示例 - 使用Click库
支持命令补全、历史记录、彩色输出等高级功能
"""

import click
from click_repl import register_repl
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


# 主命令组
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """AI Context 交互式命令行工具"""
    if ctx.invoked_subcommand is None:
        # 如果没有子命令，进入交互模式
        ctx.invoke(interactive)


@cli.command()
def interactive():
    """进入交互模式"""
    console.print("[bold green]🤖 AI Context Manager v1.0[/bold green]")
    console.print("输入 [cyan]help[/cyan] 查看命令，[cyan]exit[/cyan] 退出\n")

    # 命令映射
    commands = {
        "help": show_help,
        "status": show_status,
        "task": manage_task,
        "chat": chat_mode,
        "clear": clear_screen,
    }

    while True:
        # 使用 Rich 的 Prompt 获取输入
        user_input = Prompt.ask("[bold yellow]ai-context[/bold yellow]").strip()

        if user_input.lower() in ["exit", "quit", "q"]:
            console.print("[green]👋 感谢使用，再见！[/green]")
            break

        # 解析命令和参数
        parts = user_input.split()
        if not parts:
            continue

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # 执行命令
        if cmd in commands:
            try:
                commands[cmd](args)
            except Exception as e:
                console.print(f"[red]错误: {e}[/red]")
        else:
            console.print(f"[red]未知命令: {cmd}[/red]")
            console.print("输入 [cyan]help[/cyan] 查看可用命令")


def show_help(args):
    """显示帮助信息"""
    table = Table(title="可用命令")
    table.add_column("命令", style="cyan")
    table.add_column("描述", style="white")

    table.add_row("help", "显示此帮助信息")
    table.add_row("status", "查看项目状态")
    table.add_row("task [list|add|complete]", "任务管理")
    table.add_row("chat", "进入AI对话模式")
    table.add_row("clear", "清屏")
    table.add_row("exit", "退出程序")

    console.print(table)


def show_status(args):
    """显示项目状态"""
    console.print("\n[bold]📊 项目状态[/bold]")

    # 创建状态表格
    table = Table()
    table.add_column("状态", style="cyan")
    table.add_column("数量", justify="right")
    table.add_column("百分比", justify="right")

    table.add_row("待处理", "15", "30%")
    table.add_row("进行中", "8", "16%")
    table.add_row("已完成", "27", "54%")

    console.print(table)
    console.print("\n总进度: [green]54%[/green] ████████░░░░░░░\n")


def manage_task(args):
    """任务管理功能"""
    if not args:
        console.print("[yellow]用法: task [list|add|complete] [参数][/yellow]")
        return

    action = args[0]

    if action == "list":
        console.print("\n[bold]📋 当前任务[/bold]")
        tasks = [
            ("task-1", "实现TODO解析器", "进行中", "high"),
            ("task-2", "添加状态机", "待处理", "medium"),
            ("task-3", "编写测试", "待处理", "low"),
        ]

        for task_id, desc, status, priority in tasks:
            status_color = {"进行中": "yellow", "待处理": "blue", "已完成": "green"}.get(status, "white")

            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "")

            console.print(f"  {priority_icon} [{status_color}]{task_id}[/{status_color}]: {desc} [{status}]")

    elif action == "add":
        if len(args) < 2:
            desc = Prompt.ask("任务描述")
        else:
            desc = " ".join(args[1:])
        console.print(f"[green]✅ 添加任务: {desc}[/green]")

    elif action == "complete":
        if len(args) < 2:
            task_id = Prompt.ask("任务ID")
        else:
            task_id = args[1]
        console.print(f"[green]✅ 完成任务: {task_id}[/green]")


def chat_mode(args):
    """AI对话模式"""
    console.print("\n[bold cyan]💬 进入AI对话模式[/bold cyan]")
    console.print("[dim]输入 /exit 返回主菜单[/dim]\n")

    # 对话历史
    history = []

    while True:
        # 获取用户输入
        user_msg = Prompt.ask("[blue]您[/blue]")

        if user_msg.lower() == "/exit":
            console.print("[yellow]退出对话模式[/yellow]\n")
            break

        # 添加到历史
        history.append(("user", user_msg))

        # 模拟AI响应
        ai_response = process_ai_query(user_msg, history)
        console.print(f"[green]AI[/green]: {ai_response}\n")

        history.append(("ai", ai_response))


def process_ai_query(query, history):
    """处理AI查询（这里是模拟）"""
    responses = {
        "你好": "你好！我是AI Context助手，有什么可以帮助您的？",
        "状态": "当前项目进度54%，有8个任务正在进行中。",
        "帮助": "我可以帮您管理任务、查看项目状态、回答技术问题等。",
    }

    # 简单的关键词匹配
    for keyword, response in responses.items():
        if keyword in query:
            return response

    return f"我理解您想了解关于 '{query}' 的信息。这是一个交互式CLI的演示。"


def clear_screen(args):
    """清屏"""
    click.clear()
    console.print("[bold green]🤖 AI Context Manager v1.0[/bold green]\n")


# 额外的CLI命令（非交互模式）
@cli.command()
@click.option("--format", "-f", type=click.Choice(["json", "yaml", "table"]), default="table")
def status(format):
    """查看项目状态（命令行模式）"""
    if format == "table":
        show_status([])
    elif format == "json":
        import json

        data = {"pending": 15, "in_progress": 8, "completed": 27, "progress": 0.54}
        console.print(json.dumps(data, indent=2))


@cli.command()
@click.argument("task_id")
@click.option("--status", "-s", type=click.Choice(["pending", "in_progress", "completed"]))
def update(task_id, status):
    """更新任务状态（命令行模式）"""
    console.print(f"[green]✅ 更新任务 {task_id} 状态为 {status}[/green]")


# 注册REPL支持（可选）
register_repl(cli)

if __name__ == "__main__":
    cli()
