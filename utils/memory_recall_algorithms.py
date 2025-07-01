"""
高级记忆召回算法模块

实现智能的记忆检索功能，包括：
- 语义相似度匹配
- 思维模式匹配
- 上下文感知检索
- 多维度评分融合
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

from .intelligent_memory_retrieval import get_memory_index, intelligent_recall_memory as base_recall
from .thinking_patterns import thinking_registry

logger = logging.getLogger(__name__)


class MemoryRecallEngine:
    """
    高级记忆召回引擎
    
    提供多种智能检索算法，支持：
    - 关键词的语义匹配
    - 思维模式的相关性匹配
    - 上下文的相似度计算
    - 多维度的综合评分
    """
    
    def __init__(self):
        self.index = get_memory_index()
        self.pattern_cache = {}  # 缓存思维模式解析结果
        
    def semantic_keyword_match(self, query: str, content: str) -> float:
        """
        语义关键词匹配算法
        
        不仅匹配精确的关键词，还考虑：
        - 同义词和相关词
        - 词干提取
        - 模糊匹配
        - 上下文权重
        """
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 1. 精确匹配
        if query_lower in content_lower:
            # 计算位置权重（越靠前权重越高）
            position = content_lower.find(query_lower)
            position_weight = 1.0 - (position / max(len(content_lower), 1)) * 0.3
            return 0.8 * position_weight
        
        # 2. 分词匹配
        query_words = self._tokenize(query_lower)
        content_words = self._tokenize(content_lower)
        
        if not query_words:
            return 0.0
            
        # 计算词汇覆盖率
        matched_words = sum(1 for word in query_words if word in content_words)
        word_coverage = matched_words / len(query_words)
        
        # 3. 模糊匹配（编辑距离）
        fuzzy_score = 0.0
        for q_word in query_words:
            best_match = 0.0
            for c_word in content_words:
                similarity = SequenceMatcher(None, q_word, c_word).ratio()
                if similarity > 0.8:  # 80%相似度阈值
                    best_match = max(best_match, similarity)
            fuzzy_score += best_match
        
        if query_words:
            fuzzy_score /= len(query_words)
        
        # 4. 语义相关性（基于预定义的相关词表）
        semantic_score = self._calculate_semantic_relevance(query_words, content_words)
        
        # 综合评分
        final_score = (
            word_coverage * 0.5 +      # 词汇覆盖权重
            fuzzy_score * 0.3 +        # 模糊匹配权重
            semantic_score * 0.2       # 语义相关权重
        )
        
        return min(1.0, final_score)
    
    def thinking_pattern_match(self, memory_content: str, target_patterns: Optional[List[str]] = None) -> float:
        """
        思维模式匹配算法
        
        分析记忆内容是否包含特定的思维模式特征
        """
        # 提取内容中的思维模式特征
        detected_patterns = self._extract_thinking_patterns(memory_content)
        
        if not detected_patterns:
            return 0.0
            
        if target_patterns:
            # 计算与目标模式的匹配度
            matched = sum(1 for p in target_patterns if p in detected_patterns)
            return matched / len(target_patterns)
        else:
            # 如果没有指定目标模式，返回模式丰富度评分
            # 包含越多种思维模式的记忆价值越高
            total_patterns = len(thinking_registry.get_all_patterns())
            richness = len(detected_patterns) / total_patterns if total_patterns > 0 else 0
            return min(1.0, richness * 2)  # 放大系数，鼓励模式多样性
    
    def context_similarity(self, memory: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        上下文相似度计算
        
        考虑多个维度：
        - 时间接近度
        - 标签重叠度
        - 类型匹配度
        - 层级相关性
        - 重要性对齐
        """
        score = 0.0
        weights = {
            'time': 0.2,
            'tags': 0.3,
            'type': 0.2,
            'layer': 0.1,
            'importance': 0.2
        }
        
        memory_meta = memory.get('metadata', {})
        
        # 1. 时间接近度
        if context.get('timestamp') and memory.get('timestamp'):
            try:
                ctx_time = datetime.fromisoformat(context['timestamp'].replace('Z', '+00:00'))
                mem_time = datetime.fromisoformat(memory['timestamp'].replace('Z', '+00:00'))
                
                # 计算时间差（小时）
                time_diff = abs((ctx_time - mem_time).total_seconds()) / 3600
                
                # 使用指数衰减函数
                if time_diff < 24:  # 24小时内
                    time_score = 1.0
                elif time_diff < 168:  # 1周内
                    time_score = 0.8
                elif time_diff < 720:  # 1月内
                    time_score = 0.5
                else:
                    time_score = 0.2
                    
                score += weights['time'] * time_score
            except Exception:
                pass
        
        # 2. 标签重叠度（Jaccard相似系数）
        ctx_tags = set(context.get('tags', []))
        mem_tags = set(memory_meta.get('tags', []))
        
        if ctx_tags and mem_tags:
            tag_similarity = len(ctx_tags & mem_tags) / len(ctx_tags | mem_tags)
            score += weights['tags'] * tag_similarity
        elif not ctx_tags and not mem_tags:
            # 都没有标签也算一种匹配
            score += weights['tags'] * 0.5
        
        # 3. 类型匹配度
        if context.get('type') and memory_meta.get('type'):
            type_match = 1.0 if context['type'] == memory_meta['type'] else 0.3
            score += weights['type'] * type_match
        
        # 4. 层级相关性
        if context.get('layer') and memory.get('layer'):
            layer_scores = {
                ('global', 'global'): 1.0,
                ('project', 'project'): 1.0,
                ('session', 'session'): 1.0,
                ('global', 'project'): 0.7,
                ('project', 'global'): 0.7,
                ('global', 'session'): 0.3,
                ('session', 'global'): 0.3,
                ('project', 'session'): 0.5,
                ('session', 'project'): 0.5,
            }
            layer_match = layer_scores.get(
                (context['layer'], memory['layer']), 0.5
            )
            score += weights['layer'] * layer_match
        
        # 5. 重要性对齐
        importance_map = {'high': 3, 'medium': 2, 'low': 1}
        ctx_importance = importance_map.get(context.get('importance', 'medium'), 2)
        mem_importance = importance_map.get(memory_meta.get('importance', 'medium'), 2)
        
        # 重要性差异越小，得分越高
        importance_diff = abs(ctx_importance - mem_importance)
        importance_score = 1.0 - (importance_diff / 2)
        score += weights['importance'] * importance_score
        
        return min(1.0, score)
    
    def advanced_recall(
        self,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        thinking_patterns: Optional[List[str]] = None,
        semantic_threshold: float = 0.3,
        pattern_threshold: float = 0.2,
        context_weight: float = 0.3,
        limit: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        高级记忆召回
        
        整合多种算法进行智能检索：
        1. 基础检索（使用现有的索引系统）
        2. 语义关键词匹配
        3. 思维模式匹配
        4. 上下文相似度计算
        5. 综合评分和排序
        """
        # 1. 使用基础召回获取候选集
        candidates = base_recall(
            query=query,
            limit=limit * 3,  # 获取更多候选以便筛选
            **kwargs
        )
        
        if not candidates:
            return []
        
        # 2. 对每个候选记忆进行高级评分
        scored_memories = []
        
        for memory in candidates:
            # 基础相关性分数
            base_score = memory.get('relevance_score', 0.5)
            
            # 语义匹配分数
            semantic_score = 0.0
            if query:
                content = str(memory.get('content', ''))
                semantic_score = self.semantic_keyword_match(query, content)
            
            # 思维模式匹配分数
            pattern_score = 0.0
            if thinking_patterns:
                content = str(memory.get('content', ''))
                pattern_score = self.thinking_pattern_match(content, thinking_patterns)
            
            # 上下文相似度分数
            context_score = 0.0
            if context:
                context_score = self.context_similarity(memory, context)
            
            # 综合评分
            # 动态调整权重
            total_weight = 1.0
            weights = {'base': 0.4}
            
            if semantic_score > semantic_threshold:
                weights['semantic'] = 0.3
                total_weight += 0.3
            
            if pattern_score > pattern_threshold:
                weights['pattern'] = 0.2
                total_weight += 0.2
                
            if context_score > 0:
                weights['context'] = context_weight
                total_weight += context_weight
            
            # 归一化权重
            for key in weights:
                weights[key] /= total_weight
            
            # 计算最终分数
            final_score = (
                weights.get('base', 0) * base_score +
                weights.get('semantic', 0) * semantic_score +
                weights.get('pattern', 0) * pattern_score +
                weights.get('context', 0) * context_score
            )
            
            # 添加详细的评分信息
            memory['advanced_scores'] = {
                'base': base_score,
                'semantic': semantic_score,
                'pattern': pattern_score,
                'context': context_score,
                'final': final_score
            }
            memory['relevance_score'] = final_score
            
            scored_memories.append(memory)
        
        # 3. 按最终分数排序并返回
        scored_memories.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return scored_memories[:limit]
    
    def _tokenize(self, text: str) -> List[str]:
        """分词处理"""
        # 简单的分词实现，可以根据需要扩展
        # 去除标点符号，按空格分词
        words = re.findall(r'\w+', text.lower())
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for'}
        return [w for w in words if w not in stop_words and len(w) > 2]
    
    def _calculate_semantic_relevance(self, query_words: List[str], content_words: List[str]) -> float:
        """计算语义相关性"""
        # 定义一些简单的语义相关词组
        semantic_groups = {
            'bug': ['error', 'issue', 'problem', 'fault', 'defect', 'bug', 'crash'],
            'feature': ['feature', 'function', 'capability', 'enhancement', 'addition'],
            'performance': ['performance', 'speed', 'optimization', 'efficient', 'fast', 'slow'],
            'security': ['security', 'auth', 'authentication', 'permission', 'access', 'vulnerability'],
            'test': ['test', 'testing', 'unit', 'integration', 'coverage', 'assertion'],
            'refactor': ['refactor', 'cleanup', 'reorganize', 'restructure', 'improve'],
            'database': ['database', 'db', 'sql', 'query', 'table', 'schema'],
            'api': ['api', 'endpoint', 'request', 'response', 'rest', 'graphql'],
        }
        
        # 反向索引
        word_to_group = {}
        for group, words in semantic_groups.items():
            for word in words:
                if word not in word_to_group:
                    word_to_group[word] = []
                word_to_group[word].append(group)
        
        # 查找查询词所属的语义组
        query_groups = set()
        for word in query_words:
            if word in word_to_group:
                query_groups.update(word_to_group[word])
        
        if not query_groups:
            return 0.0
        
        # 计算内容词与查询语义组的匹配度
        matched_groups = set()
        for word in content_words:
            if word in word_to_group:
                groups = word_to_group[word]
                matched_groups.update(g for g in groups if g in query_groups)
        
        return len(matched_groups) / len(query_groups) if query_groups else 0.0
    
    def _extract_thinking_patterns(self, content: str) -> Set[str]:
        """从内容中提取思维模式特征"""
        detected_patterns = set()
        content_lower = content.lower()
        
        # 定义思维模式的特征词
        pattern_keywords = {
            'first_principles': ['first principle', '基本原理', 'fundamental', '本质'],
            'dialectical': ['dialectic', '辩证', 'contradiction', '矛盾', 'synthesis'],
            'systems_thinking': ['system', '系统', 'interconnect', '相互关联', 'holistic'],
            'critical_analysis': ['critical', '批判', 'analyze', '分析', 'evaluate'],
            'creative_exploration': ['creative', '创造', 'innovative', '创新', 'brainstorm'],
            'meta_cognitive': ['meta', '元认知', 'think about thinking', '思考的思考'],
            'analogical': ['analogy', '类比', 'similar to', '相似', 'like'],
            'empirical': ['empirical', '实证', 'evidence', '证据', 'data'],
            'pragmatic': ['pragmatic', '实用', 'practical', '实际', 'actionable'],
            'holistic': ['holistic', '整体', 'comprehensive', '全面', 'complete'],
        }
        
        # 检查每种模式的特征词
        for pattern, keywords in pattern_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_patterns.add(pattern)
        
        # 额外检查：基于内容结构
        if '1.' in content and '2.' in content:  # 有序列表
            detected_patterns.add('structured')
        
        if '?' in content:  # 包含问题
            detected_patterns.add('socratic')
        
        if 'if' in content_lower and 'then' in content_lower:  # 条件逻辑
            detected_patterns.add('logical')
        
        return detected_patterns


# 全局实例
_recall_engine: Optional[MemoryRecallEngine] = None


def get_recall_engine() -> MemoryRecallEngine:
    """获取或创建召回引擎实例"""
    global _recall_engine
    if _recall_engine is None:
        _recall_engine = MemoryRecallEngine()
    return _recall_engine


def advanced_memory_recall(
    query: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    thinking_patterns: Optional[List[str]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    便捷的高级记忆召回接口
    
    Args:
        query: 搜索查询
        context: 上下文信息（标签、类型、层级等）
        thinking_patterns: 要匹配的思维模式列表
        **kwargs: 其他参数传递给召回引擎
        
    Returns:
        匹配的记忆列表，按相关性排序
    """
    engine = get_recall_engine()
    return engine.advanced_recall(
        query=query,
        context=context,
        thinking_patterns=thinking_patterns,
        **kwargs
    )