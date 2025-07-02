# Enhanced Memory System Guide

## Overview

The Zen MCP Server now features an advanced memory system with intelligent multi-dimensional indexing, enabling fast and accurate retrieval of stored knowledge across different contexts and time spans.

## Key Features

### 1. Multi-Dimensional Indexing

The memory system indexes each memory entry across multiple dimensions:

- **Tags**: Descriptive labels for categorization
- **Type**: Memory classification (bug, feature, decision, architecture, etc.)
- **Time**: Temporal indexing with date-based bucketing
- **Quality**: Automatic quality scoring (0.0 to 1.0)
- **Layer**: Three-tier architecture (global, project, session)

### 2. Intelligent Auto-Tagging

When saving memories, the system automatically analyzes content and adds relevant tags:

- Programming languages (python, javascript, etc.)
- Topics (bug, feature, refactor, test, security, performance)
- Architectural concepts
- Domain-specific keywords

### 3. Quality Scoring Algorithm

Each memory receives a quality score based on:

- **Age**: Newer memories score higher (configurable decay)
- **Content**: Length and structure affect quality
- **Metadata**: Complete metadata improves score
- **Access Frequency**: Popular memories score higher
- **Importance**: User-specified importance level

### 4. Relevance-Based Retrieval

When recalling memories, the system calculates relevance scores considering:

- Query text matching
- Tag similarity (Jaccard coefficient)
- Type matching
- Recency bonus
- Base quality score

## Usage Examples

### Basic Save with Tags

```bash
# Save a bug report with tags and type
memory save \
  --content "Fixed null pointer exception in user authentication module" \
  --tags "bug,authentication,critical" \
  --type "bug" \
  --importance "high" \
  --layer "project"
```

### Advanced Recall with Filters

```bash
# Find all critical bugs from the last week
memory recall \
  --tags "bug,critical" \
  --type "bug" \
  --time_range "2024-01-24,2024-01-31" \
  --min_quality 0.5 \
  --limit 10
```

### Tag-Based Search

```bash
# Find all Python-related architecture decisions
memory recall \
  --tags "python,architecture" \
  --match_mode "all" \
  --layer "global"
```

### Time-Range Queries

```bash
# Get all memories from the last 30 days
memory recall \
  --time_range "2024-01-01,2024-01-31" \
  --min_quality 0.3
```

## Configuration

### Environment Variables

```bash
# Enable/disable enhanced memory
ENABLE_ENHANCED_MEMORY=true

# Memory decay settings
MEMORY_DECAY_ENABLED=true
MEMORY_DECAY_DAYS=30

# Quality threshold for cleanup
MEMORY_QUALITY_THRESHOLD=0.3

# Memory storage limits
MEMORY_GLOBAL_MAX_ITEMS=10000
MEMORY_PROJECT_MAX_ITEMS=5000
MEMORY_SESSION_MAX_ITEMS=1000
```

## Memory Actions

### Save
Store new memory with intelligent indexing:
- Automatic layer detection based on content
- Auto-tagging for better organization
- Quality score calculation
- Multi-dimensional indexing

### Recall
Retrieve memories using advanced filters:
- Multi-criteria search
- Relevance ranking
- Quality filtering
- Cross-layer search capability

### Analyze
Get insights about your memory system:
- Distribution statistics
- Tag frequency analysis
- Quality metrics
- Access patterns
- Usage recommendations

### Rebuild Index
Reconstruct search indexes:
- Useful after manual edits
- Optimizes search performance
- Updates quality scores

### Cleanup
Remove old, low-quality memories:
- Configurable age threshold
- Quality-based filtering
- Preserves important knowledge

## Best Practices

### 1. Use Descriptive Tags
- Be specific: use "python-auth-bug" instead of just "bug"
- Include context: "production", "development", "testing"
- Add domain tags: "frontend", "backend", "database"

### 2. Set Appropriate Types
- **bug**: Issues, errors, problems
- **feature**: New functionality, enhancements
- **decision**: Architectural choices, design decisions
- **architecture**: System design, patterns
- **documentation**: Notes, explanations
- **todo**: Tasks, reminders

### 3. Layer Selection
- **Global**: Universal knowledge, best practices, patterns
- **Project**: Project-specific bugs, features, configurations
- **Session**: Temporary notes, current task context

### 4. Importance Levels
- **High**: Critical information, blockers, key decisions
- **Medium**: Regular features, standard bugs
- **Low**: Minor issues, nice-to-have features

## Advanced Features

### 1. Combined Filters
Combine multiple search criteria for precise results:
```bash
memory recall \
  --query "authentication" \
  --tags "security" \
  --type "bug" \
  --layer "project" \
  --min_quality 0.6
```

### 2. Match Modes
- **any**: Match at least one tag (OR operation)
- **all**: Match all specified tags (AND operation)

### 3. Quality Management
- Memories decay over time (configurable)
- Access frequency boosts quality
- Important memories preserved longer
- Automatic cleanup of low-quality entries

## Troubleshooting

### Index Issues
If search results seem incorrect:
```bash
memory rebuild_index
```

### Storage Cleanup
To free up space:
```bash
memory cleanup
```

### Performance Tips
1. Use specific tags for faster retrieval
2. Set appropriate quality thresholds
3. Regular cleanup maintains performance
4. Limit result sets for large queries

## Integration with Other Tools

The enhanced memory system integrates seamlessly with other Zen tools:

- **thinkdeep**: Recalls relevant memories during analysis
- **debug**: Searches for similar past issues
- **codereview**: References architectural decisions
- **planner**: Uses past project patterns

## Future Enhancements

Planned improvements include:
- Semantic search using embeddings
- Memory clustering and relationships
- Cross-project memory sharing
- Memory export/import functionality
- Visual memory maps