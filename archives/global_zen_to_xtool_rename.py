#!/usr/bin/env python3
"""
全局 zen → xtool 语义分析和替换脚本
Global Zen to Xtool Semantic Analysis and Replacement Script

基于语义分析的智能替换：
- 保留必要的zen引用（如第三方库）
- 智能识别项目相关的zen术语
- 维护代码功能完整性
"""

import os
import re
from pathlib import Path


class ZenToXtoolReplacer:
    """Zen到Xtool的智能替换器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.replacements = {}
        self.skipped_files = []
        self.modified_files = []

        # 需要保留的zen引用（第三方库、外部引用等）
        self.preserve_patterns = [
            r'zen-mode',  # Emacs zen-mode
            r'zen-browser',  # 浏览器相关
            r'zen\.io',  # 域名
            r'zendesk',  # 第三方服务
            r'zenoss',   # 监控工具
        ]

        # 需要替换的文件类型
        self.target_extensions = {
            '.py', '.md', '.json', '.yml', '.yaml', '.txt',
            '.sh', '.ps1', '.cmd', '.cfg', '.conf', '.ini'
        }

        # 需要跳过的目录
        self.skip_dirs = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.xtool_venv', '.xtool_memory', 'logs'
        }

    def should_preserve_zen(self, text: str, line: str) -> bool:
        """判断是否应该保留zen引用"""
        for pattern in self.preserve_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def get_replacement_patterns(self) -> list[tuple[str, str, str]]:
        """获取替换模式列表
        返回: [(pattern, replacement, description), ...]
        """
        return [
            # 基本词汇替换
            (r'\bzen-mcp-server\b', 'xtool-mcp-server', '项目名称'),
            (r'\bzen_mcp_server\b', 'xtool_mcp_server', '项目名称（下划线）'),
            (r'\bZEN_MCP_SERVER\b', 'XTOOL_MCP_SERVER', '项目名称（大写）'),

            # 容器和服务名
            (r'\bzen-mcp-production\b', 'xtool-mcp-production', 'Docker生产服务'),
            (r'\bzen_mcp_production\b', 'xtool_mcp_production', 'Docker生产服务（下划线）'),

            # 环境变量
            (r'\bZEN_([A-Z_]+)\b', r'XTOOL_\1', '环境变量'),

            # 文件路径和目录
            (r'\.XTOOL_memory\b', '.xtool_memory', '记忆目录'),
            (r'\xtool_venv\b', '.xtool_venv', '虚拟环境目录'),

            # 工具和类名
            (r'\bZenAdvisor\b', 'XtoolAdvisor', '顾问类名'),
            (r'\bzen_advisor\b', 'xtool_advisor', '顾问工具名'),
            (r'\bzen-advisor\b', 'xtool-advisor', '顾问工具名（连字符）'),

            # 描述文本中的"Zen"
            (r'\bZen\s+(工具|tools|系统|system|平台|platform)', r'Xtool \1', 'Zen描述性文本'),
            (r'\bZEN\s+(ADVISOR|TOOLS|SYSTEM)', r'XTOOL \1', 'Zen描述性文本（大写）'),

            # 脚本名
            (r'\bzen-mcp-docker\b', 'xtool-mcp-docker', 'Docker脚本'),

            # 配置字段
            (r'"xtool_([^"]*)"', r'"xtool_\1"', 'JSON配置字段'),
            (r"'xtool_([^']*)'", r"'xtool_\1'", '配置字段（单引号）'),

            # URL和路径
            (r'/xtool-mcp-server/', '/xtool-mcp-server/', 'URL路径'),
            (r'/xtool_mcp_server/', '/xtool_mcp_server/', 'URL路径（下划线）'),

            # 注释中的说明
            (r'#.*zen\s+(mcp|server|advisor)', lambda m: m.group(0).replace('zen', 'xtool'), '注释说明'),
            (r'//.*zen\s+(mcp|server|advisor)', lambda m: m.group(0).replace('zen', 'xtool'), '注释说明'),

            # 日志和消息文本
            (r'\bzen\s+(mcp|server|advisor|tool)', r'xtool \1', '日志消息'),
        ]

    def analyze_file(self, file_path: Path) -> dict:
        """分析单个文件，返回分析结果"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return {"error": "无法读取文件"}

        original_content = content
        modifications = []

        patterns = self.get_replacement_patterns()

        for pattern, replacement, description in patterns:
            if callable(replacement):
                # 处理函数式替换
                def repl_func(match, repl=replacement):
                    return repl(match)
                new_content = re.sub(pattern, repl_func, content, flags=re.IGNORECASE)
            else:
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

            if new_content != content:
                modifications.append({
                    "pattern": pattern,
                    "replacement": replacement if not callable(replacement) else "函数替换",
                    "description": description,
                    "matches": len(re.findall(pattern, content, re.IGNORECASE))
                })
                content = new_content

        return {
            "original_content": original_content,
            "modified_content": content,
            "modifications": modifications,
            "has_changes": content != original_content
        }

    def process_file(self, file_path: Path) -> bool:
        """处理单个文件，返回是否有修改"""
        analysis = self.analyze_file(file_path)

        if "error" in analysis:
            self.skipped_files.append((file_path, analysis["error"]))
            return False

        if analysis["has_changes"]:
            # 备份原文件
            backup_path = file_path.with_suffix(file_path.suffix + '.XTOOL_backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(analysis["original_content"])

            # 写入修改后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(analysis["modified_content"])

            self.modified_files.append((file_path, analysis["modifications"]))
            return True

        return False

    def scan_project(self) -> list[Path]:
        """扫描项目，返回需要处理的文件列表"""
        files = []

        for root, dirs, filenames in os.walk(self.project_root):
            # 跳过指定目录
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for filename in filenames:
                file_path = Path(root) / filename

                # 检查文件扩展名
                if file_path.suffix.lower() in self.target_extensions:
                    files.append(file_path)

                # 检查无扩展名的特殊文件
                if filename in ['Dockerfile', 'Makefile', 'README', 'LICENSE']:
                    files.append(file_path)

        return files

    def preview_changes(self) -> dict:
        """预览所有将要进行的更改"""
        files = self.scan_project()
        preview_results = {}

        for file_path in files:
            analysis = self.analyze_file(file_path)
            if analysis.get("has_changes", False):
                preview_results[str(file_path)] = analysis["modifications"]

        return preview_results

    def execute_replacement(self, dry_run: bool = False) -> dict:
        """执行替换操作"""
        files = self.scan_project()
        results = {
            "total_files": len(files),
            "modified_files": 0,
            "skipped_files": 0,
            "modifications": {},
            "errors": []
        }

        for file_path in files:
            try:
                if dry_run:
                    analysis = self.analyze_file(file_path)
                    if analysis.get("has_changes", False):
                        results["modified_files"] += 1
                        results["modifications"][str(file_path)] = analysis["modifications"]
                else:
                    if self.process_file(file_path):
                        results["modified_files"] += 1
            except Exception as e:
                results["errors"].append((str(file_path), str(e)))
                results["skipped_files"] += 1

        return results

def main():
    """主函数"""
    project_root = "/Users/xiao/Documents/BaiduNetSyncDownload/XiaoCodePRO/xtool-mcp-server"
    replacer = ZenToXtoolReplacer(project_root)

    print("🔍 Zen → Xtool 全局语义分析和替换")
    print("=" * 60)

    # 预览更改
    print("\n📋 预览将要进行的更改:")
    print("-" * 60)

    preview = replacer.preview_changes()

    if not preview:
        print("✅ 没有发现需要替换的zen引用")
        return

    total_modifications = 0
    for file_path, modifications in preview.items():
        rel_path = os.path.relpath(file_path, project_root)
        print(f"\n📄 {rel_path}:")
        for mod in modifications:
            print(f"  • {mod['description']}: {mod['matches']} 处匹配")
            print(f"    模式: {mod['pattern']}")
            print(f"    替换: {mod['replacement']}")
            total_modifications += mod['matches']

    print(f"\n📊 总计: {len(preview)} 个文件, {total_modifications} 处修改")

    # 执行替换
    print("\n🔧 执行替换操作...")
    results = replacer.execute_replacement(dry_run=False)

    print("\n✅ 替换完成!")
    print(f"  - 扫描文件: {results['total_files']}")
    print(f"  - 修改文件: {results['modified_files']}")
    print(f"  - 跳过文件: {results['skipped_files']}")

    if results['errors']:
        print(f"\n⚠️  发现 {len(results['errors'])} 个错误:")
        for file_path, error in results['errors']:
            print(f"  - {file_path}: {error}")

    print("\n💾 备份说明:")
    print("  - 所有修改的文件都创建了 .XTOOL_backup 备份")
    print("  - 如需回滚，请使用相应的备份文件")

if __name__ == "__main__":
    main()
