"""
Smart Path Recommendation Algorithm

This module provides intelligent path recommendations based on project structure,
user patterns, and contextual understanding. It learns from usage patterns and
provides smart completions and suggestions.
"""

import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from utils.conversation_memory import recall_memory, save_memory
from utils.project_detector import ProjectDetector, ProjectType


class PathType(Enum):
    """Types of paths"""

    SOURCE = "source"
    TEST = "test"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    DATA = "data"
    ASSET = "asset"
    BUILD = "build"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class PathPattern:
    """Represents a learned path pattern"""

    pattern: str
    path_type: PathType
    frequency: int = 1
    last_used: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_types: list[ProjectType] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)

    def matches(self, path: str) -> bool:
        """Check if path matches this pattern"""
        # Convert pattern to regex
        regex_pattern = self.pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(regex_pattern, path))


@dataclass
class PathRecommendation:
    """A path recommendation with score"""

    path: str
    score: float
    reason: str
    path_type: PathType
    exists: bool = True


class PathIntelligence:
    """Smart path recommendation system"""

    # Common path patterns by project type
    COMMON_PATTERNS = {
        ProjectType.PYTHON: {
            PathType.SOURCE: ["*.py", "src/*.py", "lib/*.py", "app/*.py"],
            PathType.TEST: ["test*.py", "tests/*.py", "test/*.py", "*_test.py"],
            PathType.CONFIG: ["setup.py", "pyproject.toml", "*.ini", "*.cfg"],
            PathType.DOCUMENTATION: ["README*.md", "docs/*.md", "*.rst"],
        },
        ProjectType.JAVASCRIPT: {
            PathType.SOURCE: ["*.js", "src/*.js", "lib/*.js", "app/*.js"],
            PathType.TEST: ["*.test.js", "*.spec.js", "__tests__/*.js"],
            PathType.CONFIG: ["package.json", "*.config.js", ".eslintrc*"],
            PathType.BUILD: ["dist/*", "build/*", "out/*"],
        },
        ProjectType.TYPESCRIPT: {
            PathType.SOURCE: ["*.ts", "*.tsx", "src/*.ts", "src/*.tsx"],
            PathType.TEST: ["*.test.ts", "*.spec.ts", "__tests__/*.ts"],
            PathType.CONFIG: ["tsconfig.json", "*.config.ts"],
            PathType.BUILD: ["dist/*", "build/*", "lib/*"],
        },
    }

    def __init__(self):
        self.project_detector = ProjectDetector()
        self.learned_patterns: list[PathPattern] = []
        self.path_history: list[tuple[str, PathType, str]] = []  # (path, type, timestamp)
        self.context_associations: dict[str, list[str]] = defaultdict(list)
        self._load_learned_patterns()

    def recommend_paths(
        self,
        partial_path: str = "",
        context: Optional[str] = None,
        path_type: Optional[PathType] = None,
        max_recommendations: int = 10,
    ) -> list[PathRecommendation]:
        """Get smart path recommendations"""
        recommendations = []

        # Detect project environment
        project_env = self.project_detector.detect_project()

        # Get base directory and partial info
        if os.path.sep in partial_path:
            base_dir = os.path.dirname(partial_path)
            partial_name = os.path.basename(partial_path)
        else:
            base_dir = "."
            partial_name = partial_path

        # 1. Exact file matches
        recommendations.extend(self._find_exact_matches(base_dir, partial_name, path_type))

        # 2. Pattern-based recommendations
        recommendations.extend(
            self._get_pattern_recommendations(partial_path, project_env.project_type, path_type, context)
        )

        # 3. History-based recommendations
        recommendations.extend(self._get_history_recommendations(partial_path, context))

        # 4. Context-based recommendations
        if context:
            recommendations.extend(self._get_context_recommendations(context, partial_path))

        # 5. Common project paths
        recommendations.extend(self._get_common_paths(project_env, partial_path))

        # Remove duplicates and sort by score
        unique_recs = {}
        for rec in recommendations:
            if rec.path not in unique_recs or rec.score > unique_recs[rec.path].score:
                unique_recs[rec.path] = rec

        sorted_recs = sorted(unique_recs.values(), key=lambda r: r.score, reverse=True)

        return sorted_recs[:max_recommendations]

    def learn_path_usage(self, path: str, path_type: PathType, context: Optional[str] = None):
        """Learn from path usage"""
        # Add to history
        self.path_history.append((path, path_type, datetime.now(timezone.utc).isoformat()))

        # Learn pattern
        pattern = self._extract_pattern(path)
        existing = next((p for p in self.learned_patterns if p.pattern == pattern), None)

        if existing:
            existing.frequency += 1
            existing.last_used = datetime.now(timezone.utc).isoformat()
            if context and context not in existing.contexts:
                existing.contexts.append(context)
        else:
            project_env = self.project_detector.detect_project()
            new_pattern = PathPattern(
                pattern=pattern,
                path_type=path_type,
                project_types=[project_env.project_type],
                contexts=[context] if context else [],
            )
            self.learned_patterns.append(new_pattern)

        # Learn context association
        if context:
            self.context_associations[context].append(path)

        # Save learned patterns
        self._save_learned_patterns()

    def suggest_next_file(self, current_file: str, action: str = "edit") -> list[PathRecommendation]:
        """Suggest next file based on current file and action"""
        recommendations = []
        current_path = Path(current_file)

        # Common file transitions
        transitions = {
            "edit": {
                ".py": ["_test.py", "__init__.py", "setup.py"],
                ".js": [".test.js", ".spec.js", "package.json"],
                ".ts": [".test.ts", ".spec.ts", "tsconfig.json"],
                ".java": ["Test.java", "pom.xml", "build.gradle"],
                ".go": ["_test.go", "go.mod"],
                ".rs": ["mod.rs", "Cargo.toml"],
            },
            "test": {
                ".py": ["test_*.py", "*_test.py", "conftest.py"],
                ".js": ["*.test.js", "*.spec.js", "jest.config.js"],
                ".ts": ["*.test.ts", "*.spec.ts"],
                ".java": ["*Test.java", "*Tests.java"],
                ".go": ["*_test.go"],
                ".rs": ["tests.rs", "mod.rs"],
            },
            "config": {
                ".py": ["setup.py", "pyproject.toml", "requirements.txt"],
                ".js": ["package.json", ".eslintrc.js", "webpack.config.js"],
                ".ts": ["tsconfig.json", "package.json"],
                ".java": ["pom.xml", "build.gradle"],
                ".go": ["go.mod", "go.sum"],
                ".rs": ["Cargo.toml", "Cargo.lock"],
            },
        }

        # Get file extension
        ext = current_path.suffix

        # Get transition patterns
        patterns = transitions.get(action, {}).get(ext, [])

        for pattern in patterns:
            if "*" in pattern:
                # Pattern matching
                base_name = current_path.stem
                suggested = pattern.replace("*", base_name)

                # Check in same directory
                suggested_path = current_path.parent / suggested
                if suggested_path.exists():
                    recommendations.append(
                        PathRecommendation(
                            path=str(suggested_path),
                            score=0.9,
                            reason=f"Common {action} file for {ext} files",
                            path_type=PathType.TEST if action == "test" else PathType.SOURCE,
                            exists=True,
                        )
                    )

                # Check in test directories
                if action == "test":
                    for test_dir in ["tests", "test", "__tests__"]:
                        test_path = Path(test_dir) / suggested
                        if test_path.exists():
                            recommendations.append(
                                PathRecommendation(
                                    path=str(test_path),
                                    score=0.85,
                                    reason=f"Test file in {test_dir}/",
                                    path_type=PathType.TEST,
                                    exists=True,
                                )
                            )
            else:
                # Direct file suggestion
                if pattern.startswith("."):
                    # Replace extension
                    suggested_path = current_path.with_suffix(pattern)
                else:
                    # Look for file in project
                    for root, _, files in os.walk("."):
                        if pattern in files:
                            file_path = os.path.join(root, pattern)
                            recommendations.append(
                                PathRecommendation(
                                    path=file_path,
                                    score=0.8,
                                    reason=f"Related {action} file",
                                    path_type=PathType.CONFIG if action == "config" else PathType.SOURCE,
                                    exists=True,
                                )
                            )
                            break

        return recommendations

    def find_similar_files(self, reference_file: str, max_results: int = 5) -> list[PathRecommendation]:
        """Find files similar to a reference file"""
        recommendations = []
        ref_path = Path(reference_file)
        ref_name = ref_path.stem
        ref_ext = ref_path.suffix

        # Search strategies
        strategies = [
            # Same extension in same directory
            (ref_path.parent, f"*{ref_ext}", 0.9),
            # Similar name patterns
            (".", f"*{ref_name}*", 0.8),
            # Same extension in project
            (".", f"**/*{ref_ext}", 0.7),
            # Similar directory structure
            (str(ref_path.parent.parent), f"**/{ref_path.name}", 0.85),
        ]

        for search_dir, pattern, base_score in strategies:
            try:
                import glob

                matches = glob.glob(os.path.join(search_dir, pattern), recursive=True)

                for match in matches[:max_results]:
                    if match != reference_file:
                        # Calculate similarity score
                        match_path = Path(match)
                        score = base_score

                        # Boost score for similar names
                        if ref_name in match_path.stem:
                            score += 0.1

                        # Boost score for similar path depth
                        if len(match_path.parts) == len(ref_path.parts):
                            score += 0.05

                        recommendations.append(
                            PathRecommendation(
                                path=match,
                                score=min(score, 1.0),
                                reason=f"Similar to {ref_path.name}",
                                path_type=self._infer_path_type(match),
                                exists=True,
                            )
                        )
            except Exception:
                pass

        # Sort and deduplicate
        unique_recs = {}
        for rec in recommendations:
            if rec.path not in unique_recs or rec.score > unique_recs[rec.path].score:
                unique_recs[rec.path] = rec

        return sorted(unique_recs.values(), key=lambda r: r.score, reverse=True)[:max_results]

    def _find_exact_matches(
        self, base_dir: str, partial_name: str, path_type: Optional[PathType]
    ) -> list[PathRecommendation]:
        """Find exact file matches"""
        recommendations = []

        try:
            # Also search subdirectories if no directory specified
            if os.path.sep not in partial_name:
                # Search in common directories
                search_dirs = [base_dir, "src", "tests", "lib", "app"]
                for search_dir in search_dirs:
                    if os.path.exists(search_dir):
                        for item in os.listdir(search_dir):
                            if item.startswith(partial_name):
                                full_path = os.path.join(search_dir, item)
                                is_dir = os.path.isdir(full_path)

                                # Calculate score based on match quality
                                score = 0.95 if item == partial_name else 0.9
                                if is_dir:
                                    score -= 0.1

                                # Boost score if type matches
                                inferred_type = self._infer_path_type(full_path)
                                if path_type and inferred_type == path_type:
                                    score += 0.05

                                recommendations.append(
                                    PathRecommendation(
                                        path=full_path,
                                        score=score,
                                        reason="Exact match" if item == partial_name else "Prefix match",
                                        path_type=inferred_type,
                                        exists=True,
                                    )
                                )

            # Original logic for when directory is specified
            for item in os.listdir(base_dir):
                if item.startswith(partial_name):
                    full_path = os.path.join(base_dir, item)
                    is_dir = os.path.isdir(full_path)

                    # Calculate score based on match quality
                    score = 0.95 if item == partial_name else 0.9
                    if is_dir:
                        score -= 0.1

                    # Boost score if type matches
                    inferred_type = self._infer_path_type(full_path)
                    if path_type and inferred_type == path_type:
                        score += 0.05

                    recommendations.append(
                        PathRecommendation(
                            path=full_path,
                            score=score,
                            reason="Exact match" if item == partial_name else "Prefix match",
                            path_type=inferred_type,
                            exists=True,
                        )
                    )
        except Exception:
            pass

        return recommendations

    def _get_pattern_recommendations(
        self, partial_path: str, project_type: ProjectType, path_type: Optional[PathType], context: Optional[str]
    ) -> list[PathRecommendation]:
        """Get recommendations based on learned patterns"""
        recommendations = []

        # Check learned patterns
        for pattern in self.learned_patterns:
            # Filter by path type if specified
            if path_type and pattern.path_type != path_type:
                continue

            # Filter by project type
            if project_type not in pattern.project_types and pattern.project_types:
                continue

            # Filter by context
            if context and pattern.contexts and context not in pattern.contexts:
                continue

            # Check if pattern could match
            if self._could_match_pattern(partial_path, pattern.pattern):
                # Generate possible paths
                possible_paths = self._generate_paths_from_pattern(pattern.pattern, partial_path)

                for path in possible_paths:
                    score = 0.7
                    score += min(pattern.frequency / 100, 0.2)  # Frequency bonus

                    if os.path.exists(path):
                        score += 0.1

                    recommendations.append(
                        PathRecommendation(
                            path=path,
                            score=score,
                            reason=f"Matches learned pattern: {pattern.pattern}",
                            path_type=pattern.path_type,
                            exists=os.path.exists(path),
                        )
                    )

        return recommendations

    def _get_history_recommendations(self, partial_path: str, context: Optional[str]) -> list[PathRecommendation]:
        """Get recommendations based on usage history"""
        recommendations = []

        # Count recent usage
        path_counts = Counter()
        for path, _path_type, _ in self.path_history[-100:]:  # Last 100 entries
            if partial_path.lower() in path.lower():
                path_counts[path] += 1

        for path, count in path_counts.most_common(5):
            score = 0.6 + min(count / 20, 0.3)

            recommendations.append(
                PathRecommendation(
                    path=path,
                    score=score,
                    reason=f"Used {count} times recently",
                    path_type=self._infer_path_type(path),
                    exists=os.path.exists(path),
                )
            )

        return recommendations

    def _get_context_recommendations(self, context: str, partial_path: str) -> list[PathRecommendation]:
        """Get recommendations based on context"""
        recommendations = []

        # Get paths associated with context
        associated_paths = self.context_associations.get(context, [])

        for path in associated_paths:
            if partial_path.lower() in path.lower():
                recommendations.append(
                    PathRecommendation(
                        path=path,
                        score=0.75,
                        reason=f"Associated with context: {context}",
                        path_type=self._infer_path_type(path),
                        exists=os.path.exists(path),
                    )
                )

        return recommendations

    def _get_common_paths(self, project_env, partial_path: str) -> list[PathRecommendation]:
        """Get common project paths"""
        recommendations = []

        # Get patterns for project type
        patterns = self.COMMON_PATTERNS.get(project_env.project_type, {})

        for path_type, path_patterns in patterns.items():
            for pattern in path_patterns:
                if self._could_match_pattern(partial_path, pattern):
                    possible_paths = self._generate_paths_from_pattern(pattern, partial_path)

                    for path in possible_paths:
                        if os.path.exists(path):
                            recommendations.append(
                                PathRecommendation(
                                    path=path,
                                    score=0.65,
                                    reason=f"Common {project_env.project_type.value} {path_type.value} file",
                                    path_type=path_type,
                                    exists=True,
                                )
                            )

        return recommendations

    def _extract_pattern(self, path: str) -> str:
        """Extract pattern from path"""
        # Replace specific parts with wildcards
        path_obj = Path(path)

        # Keep extension
        if path_obj.suffix:
            pattern = f"*{path_obj.suffix}"
        else:
            pattern = path_obj.name

        # Add directory pattern if in subdirectory
        if path_obj.parent != Path("."):
            pattern = str(path_obj.parent / pattern)

        return pattern

    def _infer_path_type(self, path: str) -> PathType:
        """Infer the type of a path"""
        path_lower = path.lower()

        # Test files
        if any(pattern in path_lower for pattern in ["test", "spec", "_test.", ".test."]):
            return PathType.TEST

        # Config files
        if any(ext in path_lower for ext in [".json", ".yml", ".yaml", ".ini", ".toml", ".config"]):
            return PathType.CONFIG

        # Documentation
        if any(ext in path_lower for ext in [".md", ".rst", ".txt", "readme", "changelog"]):
            return PathType.DOCUMENTATION

        # Build artifacts
        if any(dir in path_lower for dir in ["/build/", "/dist/", "/out/", "/target/"]):
            return PathType.BUILD

        # Dependencies
        if any(dir in path_lower for dir in ["node_modules", "vendor", ".venv", "venv"]):
            return PathType.DEPENDENCY

        # Data files
        if any(ext in path_lower for ext in [".csv", ".json", ".xml", ".sql", ".db"]):
            return PathType.DATA

        # Assets
        if any(ext in path_lower for ext in [".png", ".jpg", ".gif", ".svg", ".css", ".scss"]):
            return PathType.ASSET

        # Default to source
        return PathType.SOURCE

    def _could_match_pattern(self, partial: str, pattern: str) -> bool:
        """Check if partial path could match pattern"""
        # Simple check - could be enhanced
        pattern_parts = pattern.replace("*", "").replace("?", "").lower()
        return any(part in partial.lower() for part in pattern_parts.split("/") if part)

    def _generate_paths_from_pattern(self, pattern: str, partial: str) -> list[str]:
        """Generate possible paths from pattern"""
        paths = []

        # Simple generation - replace wildcards with partial
        if "*" in pattern:
            # Extract non-wildcard parts
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                if partial.startswith(prefix):
                    remaining = partial[len(prefix) :]
                    paths.append(prefix + remaining + suffix)

        # Also try glob
        try:
            import glob

            matches = glob.glob(pattern)
            paths.extend(matches)
        except Exception:
            pass

        return list(set(paths))

    def _save_learned_patterns(self):
        """Save learned patterns to memory"""
        patterns_data = []
        for pattern in self.learned_patterns:
            patterns_data.append(
                {
                    "pattern": pattern.pattern,
                    "path_type": pattern.path_type.value,
                    "frequency": pattern.frequency,
                    "last_used": pattern.last_used,
                    "project_types": [pt.value for pt in pattern.project_types],
                    "contexts": pattern.contexts,
                }
            )

        save_memory(
            content=json.dumps(patterns_data),
            layer="global",
            metadata={"type": "path_patterns", "count": len(patterns_data)},
            key="learned_path_patterns",
        )

    def _load_learned_patterns(self):
        """Load learned patterns from memory"""
        memories = recall_memory(query="learned_path_patterns", filters={"type": "path_patterns"}, limit=1)

        if memories:
            content = memories[0].get("content", "[]")
            if isinstance(content, str):
                content = json.loads(content)

            for pattern_data in content:
                pattern = PathPattern(
                    pattern=pattern_data["pattern"],
                    path_type=PathType(pattern_data["path_type"]),
                    frequency=pattern_data.get("frequency", 1),
                    last_used=pattern_data.get("last_used", ""),
                    project_types=[ProjectType(pt) for pt in pattern_data.get("project_types", [])],
                    contexts=pattern_data.get("contexts", []),
                )
                self.learned_patterns.append(pattern)
