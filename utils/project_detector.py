"""
Project Environment Auto-Detection System

This module provides intelligent project type detection and environment analysis
for the Zen MCP Server. It can identify project types, dependencies, build systems,
and provide context-aware recommendations.
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from utils.conversation_memory import save_memory


class ProjectType(Enum):
    """Supported project types"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    RUBY = "ruby"
    PHP = "php"
    DOTNET = "dotnet"
    UNKNOWN = "unknown"


class BuildSystem(Enum):
    """Common build systems"""

    PIP = "pip"
    POETRY = "poetry"
    PIPENV = "pipenv"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    MAVEN = "maven"
    GRADLE = "gradle"
    GO_MOD = "go_mod"
    CARGO = "cargo"
    CMAKE = "cmake"
    MAKE = "make"
    BUNDLER = "bundler"
    COMPOSER = "composer"
    DOTNET_CLI = "dotnet_cli"
    UNKNOWN = "unknown"


@dataclass
class ProjectEnvironment:
    """Represents a detected project environment"""

    root_path: str
    project_type: ProjectType
    build_systems: list[BuildSystem] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    test_frameworks: list[str] = field(default_factory=list)
    virtual_env: Optional[str] = None
    config_files: list[str] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "root_path": self.root_path,
            "project_type": self.project_type.value,
            "build_systems": [bs.value for bs in self.build_systems],
            "languages": self.languages,
            "frameworks": self.frameworks,
            "dependencies": self.dependencies,
            "test_frameworks": self.test_frameworks,
            "virtual_env": self.virtual_env,
            "config_files": self.config_files,
            "structure": self.structure,
            "metadata": self.metadata,
        }


class ProjectDetector:
    """Detects and analyzes project environments"""

    # File patterns for project type detection
    PROJECT_INDICATORS = {
        ProjectType.PYTHON: {
            "files": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock"],
            "extensions": [".py"],
            "dirs": ["__pycache__", "venv", ".venv", "env"],
        },
        ProjectType.JAVASCRIPT: {
            "files": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
            "extensions": [".js", ".mjs", ".cjs"],
            "dirs": ["node_modules"],
        },
        ProjectType.TYPESCRIPT: {
            "files": ["tsconfig.json", "package.json"],
            "extensions": [".ts", ".tsx"],
            "dirs": ["node_modules"],
        },
        ProjectType.JAVA: {
            "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
            "extensions": [".java"],
            "dirs": ["src/main/java", "target", "build"],
        },
        ProjectType.GO: {"files": ["go.mod", "go.sum"], "extensions": [".go"], "dirs": ["vendor"]},
        ProjectType.RUST: {"files": ["Cargo.toml", "Cargo.lock"], "extensions": [".rs"], "dirs": ["target", "src"]},
        ProjectType.CPP: {
            "files": ["CMakeLists.txt", "Makefile", "configure"],
            "extensions": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
            "dirs": ["build", "cmake-build-debug"],
        },
        ProjectType.RUBY: {
            "files": ["Gemfile", "Gemfile.lock", "Rakefile"],
            "extensions": [".rb"],
            "dirs": ["vendor/bundle"],
        },
        ProjectType.PHP: {"files": ["composer.json", "composer.lock"], "extensions": [".php"], "dirs": ["vendor"]},
        ProjectType.DOTNET: {
            "files": ["*.csproj", "*.fsproj", "*.vbproj", "*.sln"],
            "extensions": [".cs", ".fs", ".vb"],
            "dirs": ["bin", "obj"],
        },
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "django": ["django", "manage.py", "settings.py"],
        "flask": ["flask", "app.py", "application.py"],
        "fastapi": ["fastapi", "uvicorn"],
        "react": ["react", "react-dom", "jsx"],
        "vue": ["vue", "@vue"],
        "angular": ["@angular/core", "angular.json"],
        "express": ["express"],
        "nextjs": ["next", "next.config.js"],
        "spring": ["spring-boot", "springframework"],
        "rails": ["rails", "config/routes.rb"],
        "laravel": ["laravel", "artisan"],
        "pytest": ["pytest", "test_*.py", "*_test.py"],
        "jest": ["jest", "jest.config.js"],
        "mocha": ["mocha"],
        "junit": ["junit", "org.junit"],
        "rspec": ["rspec", "spec_helper.rb"],
    }

    def __init__(self):
        self.project_cache = {}

    def detect_project(self, path: str = ".") -> ProjectEnvironment:
        """Detect project type and environment"""
        root_path = os.path.abspath(path)

        # Check cache
        if root_path in self.project_cache:
            return self.project_cache[root_path]

        env = ProjectEnvironment(root_path=root_path, project_type=ProjectType.UNKNOWN)

        # Detect project type
        env.project_type = self._detect_project_type(root_path)

        # Detect languages
        env.languages = self._detect_languages(root_path)

        # Detect build systems
        env.build_systems = self._detect_build_systems(root_path)

        # Detect frameworks
        env.frameworks = self._detect_frameworks(root_path)

        # Detect dependencies
        env.dependencies = self._detect_dependencies(root_path, env.project_type)

        # Detect test frameworks
        env.test_frameworks = self._detect_test_frameworks(root_path, env.frameworks)

        # Detect virtual environment
        env.virtual_env = self._detect_virtual_env(root_path)

        # Find config files
        env.config_files = self._find_config_files(root_path)

        # Analyze project structure
        env.structure = self._analyze_structure(root_path)

        # Extract metadata
        env.metadata = self._extract_metadata(root_path, env.project_type)

        # Cache result
        self.project_cache[root_path] = env

        # Save to memory
        self._save_to_memory(env)

        return env

    def _detect_project_type(self, root_path: str) -> ProjectType:
        """Detect the primary project type"""
        scores = {}

        for project_type, indicators in self.PROJECT_INDICATORS.items():
            score = 0

            # Check for indicator files
            for file_pattern in indicators.get("files", []):
                if self._file_exists(root_path, file_pattern):
                    score += 10

            # Check for file extensions
            for ext in indicators.get("extensions", []):
                if self._count_files_with_extension(root_path, ext) > 0:
                    score += 5

            # Check for directories
            for dir_name in indicators.get("dirs", []):
                if os.path.exists(os.path.join(root_path, dir_name)):
                    score += 3

            if score > 0:
                scores[project_type] = score

        if not scores:
            return ProjectType.UNKNOWN

        # Return the type with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def _detect_languages(self, root_path: str) -> list[str]:
        """Detect all programming languages used"""
        languages = set()

        # Extension to language mapping
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".m": "MATLAB",
            ".jl": "Julia",
            ".lua": "Lua",
            ".sh": "Shell",
            ".ps1": "PowerShell",
        }

        for ext, lang in ext_map.items():
            if self._count_files_with_extension(root_path, ext) > 0:
                languages.add(lang)

        return sorted(languages)

    def _detect_build_systems(self, root_path: str) -> list[BuildSystem]:
        """Detect build systems in use"""
        systems = []

        build_files = {
            "requirements.txt": BuildSystem.PIP,
            "setup.py": BuildSystem.PIP,
            "pyproject.toml": BuildSystem.POETRY,
            "poetry.lock": BuildSystem.POETRY,
            "Pipfile": BuildSystem.PIPENV,
            "Pipfile.lock": BuildSystem.PIPENV,
            "package.json": BuildSystem.NPM,
            "yarn.lock": BuildSystem.YARN,
            "pnpm-lock.yaml": BuildSystem.PNPM,
            "pom.xml": BuildSystem.MAVEN,
            "build.gradle": BuildSystem.GRADLE,
            "build.gradle.kts": BuildSystem.GRADLE,
            "go.mod": BuildSystem.GO_MOD,
            "Cargo.toml": BuildSystem.CARGO,
            "CMakeLists.txt": BuildSystem.CMAKE,
            "Makefile": BuildSystem.MAKE,
            "Gemfile": BuildSystem.BUNDLER,
            "composer.json": BuildSystem.COMPOSER,
        }

        for file_name, build_system in build_files.items():
            if self._file_exists(root_path, file_name):
                if build_system not in systems:
                    systems.append(build_system)

        # Check for .NET projects
        if any(self._file_exists(root_path, pattern) for pattern in ["*.csproj", "*.fsproj", "*.sln"]):
            systems.append(BuildSystem.DOTNET_CLI)

        return systems

    def _detect_frameworks(self, root_path: str) -> list[str]:
        """Detect frameworks in use"""
        frameworks = []

        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                # Check in dependency files
                if self._check_dependency_files(root_path, pattern):
                    frameworks.append(framework)
                    break
                # Check for specific files
                elif self._file_exists(root_path, pattern):
                    frameworks.append(framework)
                    break

        return frameworks

    def _detect_dependencies(self, root_path: str, project_type: ProjectType) -> dict[str, list[str]]:
        """Extract dependencies from dependency files"""
        dependencies = {}

        if project_type == ProjectType.PYTHON:
            dependencies.update(self._parse_python_dependencies(root_path))
        elif project_type in [ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT]:
            dependencies.update(self._parse_node_dependencies(root_path))
        elif project_type == ProjectType.JAVA:
            dependencies.update(self._parse_java_dependencies(root_path))
        elif project_type == ProjectType.GO:
            dependencies.update(self._parse_go_dependencies(root_path))
        elif project_type == ProjectType.RUST:
            dependencies.update(self._parse_rust_dependencies(root_path))

        return dependencies

    def _detect_test_frameworks(self, root_path: str, frameworks: list[str]) -> list[str]:
        """Detect test frameworks"""
        test_frameworks = []

        # Filter framework list for test frameworks
        test_framework_names = ["pytest", "jest", "mocha", "junit", "rspec"]
        test_frameworks = [f for f in frameworks if f in test_framework_names]

        # Additional detection for test directories
        if os.path.exists(os.path.join(root_path, "tests")) or os.path.exists(os.path.join(root_path, "test")):
            # Check for Python tests
            if self._count_files_with_extension(os.path.join(root_path, "tests"), ".py") > 0:
                if "pytest" not in test_frameworks:
                    test_frameworks.append("pytest")

        return test_frameworks

    def _detect_virtual_env(self, root_path: str) -> Optional[str]:
        """Detect Python virtual environment"""
        venv_dirs = ["venv", ".venv", "env", ".env", "virtualenv"]

        for venv_dir in venv_dirs:
            venv_path = os.path.join(root_path, venv_dir)
            if os.path.exists(venv_path):
                # Check if it's a valid virtual environment
                if os.path.exists(os.path.join(venv_path, "bin", "python")) or os.path.exists(
                    os.path.join(venv_path, "Scripts", "python.exe")
                ):
                    return venv_path

        # Check if we're currently in a virtual environment
        return os.environ.get("VIRTUAL_ENV")

    def _find_config_files(self, root_path: str) -> list[str]:
        """Find all configuration files"""
        config_patterns = [
            "*.config.*",
            "*.conf",
            "*.ini",
            "*.yaml",
            "*.yml",
            "*.json",
            "*.toml",
            ".*rc",
            "Dockerfile",
            "docker-compose.*",
            ".gitignore",
            ".env*",
            "Makefile",
            "*.properties",
        ]

        config_files = []
        for pattern in config_patterns:
            config_files.extend(self._find_files(root_path, pattern, max_depth=2))

        return sorted(set(config_files))

    def _analyze_structure(self, root_path: str) -> dict[str, Any]:
        """Analyze project directory structure"""
        structure = {
            "src_dirs": [],
            "test_dirs": [],
            "doc_dirs": [],
            "config_dirs": [],
            "total_files": 0,
            "total_dirs": 0,
            "max_depth": 0,
        }

        # Common directory patterns
        src_patterns = ["src", "lib", "app", "core", "pkg", "internal"]
        test_patterns = ["test", "tests", "spec", "specs", "__tests__"]
        doc_patterns = ["docs", "doc", "documentation"]
        config_patterns = ["config", "conf", ".config"]

        for item in os.listdir(root_path):
            item_path = os.path.join(root_path, item)
            if os.path.isdir(item_path):
                item_lower = item.lower()
                if any(pattern in item_lower for pattern in src_patterns):
                    structure["src_dirs"].append(item)
                elif any(pattern in item_lower for pattern in test_patterns):
                    structure["test_dirs"].append(item)
                elif any(pattern in item_lower for pattern in doc_patterns):
                    structure["doc_dirs"].append(item)
                elif any(pattern in item_lower for pattern in config_patterns):
                    structure["config_dirs"].append(item)

        # Count files and directories
        for root, dirs, files in os.walk(root_path):
            structure["total_files"] += len(files)
            structure["total_dirs"] += len(dirs)
            depth = root.replace(root_path, "").count(os.sep)
            structure["max_depth"] = max(structure["max_depth"], depth)

            # Don't go too deep
            if depth > 5:
                dirs.clear()

        return structure

    def _extract_metadata(self, root_path: str, project_type: ProjectType) -> dict[str, Any]:
        """Extract project metadata"""
        metadata = {}

        if project_type == ProjectType.PYTHON:
            metadata.update(self._extract_python_metadata(root_path))
        elif project_type in [ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT]:
            metadata.update(self._extract_node_metadata(root_path))

        # Extract from README
        readme_path = self._find_readme(root_path)
        if readme_path:
            metadata["readme"] = readme_path
            metadata["description"] = self._extract_readme_description(readme_path)

        # Extract from git
        if os.path.exists(os.path.join(root_path, ".git")):
            metadata["version_control"] = "git"
            # Could extract more git info here

        return metadata

    def _file_exists(self, root_path: str, pattern: str) -> bool:
        """Check if a file matching pattern exists"""
        if "*" in pattern:
            import glob

            return len(glob.glob(os.path.join(root_path, pattern))) > 0
        else:
            return os.path.exists(os.path.join(root_path, pattern))

    def _count_files_with_extension(self, root_path: str, ext: str) -> int:
        """Count files with given extension"""
        count = 0
        for root, _, files in os.walk(root_path):
            count += sum(1 for f in files if f.endswith(ext))
            # Don't count files in hidden or vendor directories
            if any(part.startswith(".") or part in ["node_modules", "vendor"] for part in root.split(os.sep)):
                continue
        return count

    def _find_files(self, root_path: str, pattern: str, max_depth: int = 3) -> list[str]:
        """Find files matching pattern"""
        import glob

        matches = []

        for depth in range(max_depth + 1):
            search_pattern = os.path.join(root_path, *(["*"] * depth), pattern)
            matches.extend(glob.glob(search_pattern))

        # Convert to relative paths
        return [os.path.relpath(m, root_path) for m in matches]

    def _check_dependency_files(self, root_path: str, pattern: str) -> bool:
        """Check if pattern exists in dependency files"""
        # Check package.json
        package_json = os.path.join(root_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json) as f:
                    content = f.read().lower()
                    if pattern.lower() in content:
                        return True
            except Exception:
                pass

        # Check requirements.txt
        requirements = os.path.join(root_path, "requirements.txt")
        if os.path.exists(requirements):
            try:
                with open(requirements) as f:
                    content = f.read().lower()
                    if pattern.lower() in content:
                        return True
            except Exception:
                pass

        return False

    def _parse_python_dependencies(self, root_path: str) -> dict[str, list[str]]:
        """Parse Python dependencies"""
        deps = {"runtime": [], "dev": []}

        # Parse requirements.txt
        req_file = os.path.join(root_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            deps["runtime"].append(line.split("==")[0].split(">=")[0])
            except Exception:
                pass

        # Parse pyproject.toml
        pyproject = os.path.join(root_path, "pyproject.toml")
        if os.path.exists(pyproject):
            try:
                # Simple parsing without toml library
                with open(pyproject) as f:
                    content = f.read()
                    # Extract dependencies section
                    if "[tool.poetry.dependencies]" in content:
                        in_deps = False
                        for line in content.split("\n"):
                            if "[tool.poetry.dependencies]" in line:
                                in_deps = True
                            elif in_deps and line.startswith("["):
                                break
                            elif in_deps and "=" in line:
                                dep = line.split("=")[0].strip()
                                if dep != "python":
                                    deps["runtime"].append(dep)
            except Exception:
                pass

        return deps

    def _parse_node_dependencies(self, root_path: str) -> dict[str, list[str]]:
        """Parse Node.js dependencies"""
        deps = {"runtime": [], "dev": []}

        package_json = os.path.join(root_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps["runtime"] = list(data.get("dependencies", {}).keys())
                    deps["dev"] = list(data.get("devDependencies", {}).keys())
            except Exception:
                pass

        return deps

    def _parse_java_dependencies(self, root_path: str) -> dict[str, list[str]]:
        """Parse Java dependencies"""
        deps = {"runtime": [], "dev": []}

        # Parse pom.xml (simplified)
        pom_file = os.path.join(root_path, "pom.xml")
        if os.path.exists(pom_file):
            try:
                with open(pom_file) as f:
                    content = f.read()
                    # Simple regex to find artifactIds
                    import re

                    artifacts = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
                    deps["runtime"] = list(set(artifacts))
            except Exception:
                pass

        return deps

    def _parse_go_dependencies(self, root_path: str) -> dict[str, list[str]]:
        """Parse Go dependencies"""
        deps = {"runtime": []}

        go_mod = os.path.join(root_path, "go.mod")
        if os.path.exists(go_mod):
            try:
                with open(go_mod) as f:
                    for line in f:
                        if line.strip().startswith("require"):
                            # Simple extraction
                            parts = line.split()
                            if len(parts) >= 2:
                                deps["runtime"].append(parts[1])
            except Exception:
                pass

        return deps

    def _parse_rust_dependencies(self, root_path: str) -> dict[str, list[str]]:
        """Parse Rust dependencies"""
        deps = {"runtime": [], "dev": []}

        cargo_toml = os.path.join(root_path, "Cargo.toml")
        if os.path.exists(cargo_toml):
            try:
                with open(cargo_toml) as f:
                    content = f.read()
                    in_deps = False
                    in_dev_deps = False
                    for line in content.split("\n"):
                        if "[dependencies]" in line:
                            in_deps = True
                            in_dev_deps = False
                        elif "[dev-dependencies]" in line:
                            in_deps = False
                            in_dev_deps = True
                        elif line.startswith("["):
                            in_deps = False
                            in_dev_deps = False
                        elif "=" in line:
                            dep = line.split("=")[0].strip()
                            if in_deps:
                                deps["runtime"].append(dep)
                            elif in_dev_deps:
                                deps["dev"].append(dep)
            except Exception:
                pass

        return deps

    def _find_readme(self, root_path: str) -> Optional[str]:
        """Find README file"""
        readme_patterns = ["README.md", "README.MD", "README.rst", "README.txt", "README"]

        for pattern in readme_patterns:
            readme_path = os.path.join(root_path, pattern)
            if os.path.exists(readme_path):
                return pattern

        return None

    def _extract_readme_description(self, readme_path: str) -> Optional[str]:
        """Extract description from README"""
        try:
            with open(readme_path, encoding="utf-8") as f:
                lines = f.readlines()
                # Skip title and empty lines
                for i, line in enumerate(lines):
                    if i > 0 and line.strip() and not line.startswith("#"):
                        # Return first paragraph
                        description = []
                        for j in range(i, min(i + 5, len(lines))):
                            if lines[j].strip():
                                description.append(lines[j].strip())
                            else:
                                break
                        return " ".join(description)[:200]
        except Exception:
            pass

        return None

    def _extract_python_metadata(self, root_path: str) -> dict[str, Any]:
        """Extract Python-specific metadata"""
        metadata = {}

        # Check setup.py
        setup_py = os.path.join(root_path, "setup.py")
        if os.path.exists(setup_py):
            try:
                with open(setup_py) as f:
                    content = f.read()
                    # Simple extraction
                    import re

                    name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if name_match:
                        metadata["name"] = name_match.group(1)

                    version_match = re.search(r"version\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if version_match:
                        metadata["version"] = version_match.group(1)
            except Exception:
                pass

        # Check pyproject.toml
        pyproject = os.path.join(root_path, "pyproject.toml")
        if os.path.exists(pyproject):
            try:
                with open(pyproject) as f:
                    content = f.read()
                    # Simple extraction
                    import re

                    name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
                    if name_match:
                        metadata["name"] = name_match.group(1)

                    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
                    if version_match:
                        metadata["version"] = version_match.group(1)
            except Exception:
                pass

        return metadata

    def _extract_node_metadata(self, root_path: str) -> dict[str, Any]:
        """Extract Node.js metadata"""
        metadata = {}

        package_json = os.path.join(root_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    metadata["name"] = data.get("name")
                    metadata["version"] = data.get("version")
                    metadata["description"] = data.get("description")
                    metadata["license"] = data.get("license")
                    metadata["scripts"] = list(data.get("scripts", {}).keys())
            except Exception:
                pass

        return metadata

    def _save_to_memory(self, env: ProjectEnvironment):
        """Save project environment to memory"""
        save_memory(
            content=json.dumps(env.to_dict()),
            layer="project",
            metadata={
                "type": "project_environment",
                "project_type": env.project_type.value,
                "root_path": env.root_path,
            },
            key=f"project_env_{os.path.basename(env.root_path)}",
        )

    def get_recommendations(self, env: ProjectEnvironment) -> dict[str, list[str]]:
        """Get project-specific recommendations"""
        recommendations = {"commands": [], "tools": [], "practices": []}

        # Python recommendations
        if env.project_type == ProjectType.PYTHON:
            if BuildSystem.PIP in env.build_systems:
                recommendations["commands"].append("pip install -r requirements.txt")
            if BuildSystem.POETRY in env.build_systems:
                recommendations["commands"].append("poetry install")
            if not env.virtual_env:
                recommendations["practices"].append("Create a virtual environment: python -m venv venv")
            if "pytest" in env.test_frameworks:
                recommendations["commands"].append("pytest")
                recommendations["tools"].append("pytest-cov for coverage")

        # JavaScript/TypeScript recommendations
        elif env.project_type in [ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT]:
            if BuildSystem.NPM in env.build_systems:
                recommendations["commands"].append("npm install")
                recommendations["commands"].append("npm run dev")
            if BuildSystem.YARN in env.build_systems:
                recommendations["commands"].append("yarn install")
                recommendations["commands"].append("yarn dev")
            if "jest" in env.test_frameworks:
                recommendations["commands"].append("npm test")
            if env.project_type == ProjectType.TYPESCRIPT:
                recommendations["commands"].append("tsc --watch")

        # Java recommendations
        elif env.project_type == ProjectType.JAVA:
            if BuildSystem.MAVEN in env.build_systems:
                recommendations["commands"].append("mvn clean install")
                recommendations["commands"].append("mvn test")
            if BuildSystem.GRADLE in env.build_systems:
                recommendations["commands"].append("./gradlew build")
                recommendations["commands"].append("./gradlew test")

        # General recommendations
        if ".gitignore" not in env.config_files:
            recommendations["practices"].append("Add a .gitignore file")

        if not env.test_frameworks:
            recommendations["practices"].append("Consider adding a test framework")

        return recommendations
