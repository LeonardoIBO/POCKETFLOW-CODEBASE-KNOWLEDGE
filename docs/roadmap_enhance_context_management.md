# Roadmap: Enhanced Context Management for Large Repositories

## Overview

This document outlines a strategy to enhance the PocketFlow Tutorial Codebase Knowledge system to handle large repositories that exceed LLM token limits through intelligent chunking and retry mechanisms.

## Current Problem

### Issue Description
- **Token Limit Exceeded**: Large repositories (like digifarm-api-services with 359 files) generate prompts exceeding 200,000 tokens
- **Single LLM Call Bottleneck**: The `IdentifyAbstractions` node concatenates all file contents into one massive prompt
- **No Chunking Strategy**: Current implementation lacks automatic fallback for oversized prompts
- **Account Tier Limitations**: Claude 4 Sonnet's 1M token context is only available to Tier 4+ accounts

### Error Example
```
anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'prompt is too long: 214707 tokens > 200000 maximum'}}
```

## Proposed Solution: Progressive Chunking Strategy

### Core Strategy
Implement an intelligent retry mechanism that automatically handles token limit errors by progressively reducing context size through smart file grouping and chunking.
Default model for v1 is GPT-5; initial error detection is scoped to GPT-5 token/context errors.

### Implementation Architecture

#### 1. Enhanced Error Detection (GPT-5 v1)
```python
def is_token_limit_error(exception):
    """Detect token/context limit errors (v1: GPT-5 only)."""
    error_indicators = [
        "prompt is too long",
        "maximum context length",
        "token limit exceeded",
        "context window exceeded",
        "too many tokens"
    ]
    return any(indicator in str(exception).lower() for indicator in error_indicators)
```

#### 2. Progressive Chunking Levels
When token limits are hit, implement a multi-level fallback strategy:

**Level 1: Service-Based Chunking**
- Group files by service directories (e.g., `apis/services/partial-dr/`, `apis/services/ondemand-dr/`)
- Process each service independently
- Merge abstractions with conflict resolution

**Level 2: Module-Based Chunking**
- Further split large services into modules/components
- Group related files (handlers, models, utilities)
- Maintain dependency tracking


#### 3. Enhanced `IdentifyAbstractions` Node

```python
class IdentifyAbstractions(Node):
    def exec_fallback(self, prep_res, exc):
        """Intelligent fallback for token limit errors"""
        if self.is_token_limit_error(exc):
            return self.progressive_chunking_strategy(prep_res)
        raise exc
    
    def progressive_chunking_strategy(self, prep_res):
        """Implement multi-level chunking strategy (service -> module)."""
        # Use precomputed per-file token estimates from the estimator
        # to aggregate by service and module, then run subflows within limits.
        # Level 1: Service-based chunking
        # Level 2: Module-based chunking
        pass
```

### Chunking Strategy Details

#### Service-Based Grouping
```python
service_groups = {
    "partial-dr": ["apis/services/partial-dr/**"],
    "ondemand-dr": ["apis/services/ondemand-dr/**"],
    "field-delineation": ["apis/services/fieldDelineation/**"],
    "client-datasets": ["apis/services/clientExposedDatasets/**"],
    "core-libs": ["apis/libs/**"],
    "infrastructure": ["infrastructure/**"]
}
```

#### Smart File Prioritization
1. **Core Architecture Files**: Main application files, configuration
2. **Service Entry Points**: Handler files, main service logic
3. **Data Models**: Database models, schemas
4. **Utilities**: Helper functions, utilities
5. **Tests**: Process last or exclude based on patterns

#### Context Preservation Techniques
- **Cross-Chunk References**: Maintain file index mapping across chunks
- **Dependency Tracking**: Track inter-service dependencies
- **Abstraction Merging**: Intelligent merging of related abstractions from different chunks
- **Hierarchy Maintenance**: Preserve architectural relationships

## Implementation Plan

### Phase 1: Foundation (Immediate)
1. **Error Detection Enhancement**
   - Add token limit error detection utility (v1: GPT-5 only)
   - Enhance error logging for debugging

2. **File Grouping Logic**
   - Implement service/module detection from file paths
   - Create file grouping utilities
   - Add configurable grouping strategies

3. **Token Estimator Integration**
   - Run estimator preflight; store `sum_file_tokens`, `overhead_tokens`, `total_tokens`
   - Persist per-file token estimates into shared store for grouping by service/module
   - Use estimator outputs to guide chunk boundaries before retries

### Phase 2: Chunking Strategy (Week 1)
1. **Progressive Chunking Implementation**
   - Implement `exec_fallback` in `IdentifyAbstractions`
   - Add service-based chunking logic
   - Create group token aggregation utilities (sum per service/module vs threshold)

2. **Context Management**
   - Implement cross-chunk reference tracking
   - Add abstraction merging logic
   - Create dependency preservation mechanisms

### Phase 3: Advanced Features (Week 2)
1. **Smart Optimization**
   - Leverage estimator data for adaptive chunk sizing (GPT-5 default)
   - Implement adaptive chunk sizing
   - Create context window optimization

2. **Conflict Resolution**
   - Handle duplicate abstractions across chunks
   - Implement abstraction relationship merging
   - Add validation for merged results

### Phase 4: Testing & Refinement (Week 3)
1. **Comprehensive Testing**
   - Test with various repository sizes
   - Validate chunking strategies
   - Performance optimization

2. **Configuration Options**
   - Add user-configurable chunking strategies
   - Implement chunk size parameters
   - Create fallback behavior options

## Benefits

### Immediate Benefits
- **Large Repository Support**: Handle repositories of any size
- **Automatic Fallback**: No manual intervention required
- **Robust Processing**: Graceful degradation under token limits

### Long-term Benefits
- **Scalability**: Support for enterprise-scale codebases
- **Cost Optimization**: Efficient token usage across LLM providers
- **Provider Flexibility**: Work with different LLM token limits
- **User Experience**: Seamless processing regardless of repository size

## Configuration Options

### User-Configurable Parameters
```bash
# Chunking strategy options
python main.py --repo <url> --chunking-strategy service|module
python main.py --repo <url> --max-chunk-tokens 140000
python main.py --repo <url> --chunk-overlap 10000
python main.py --repo <url> --priority-patterns "*/handlers/*,*/models/*"
```

### Environment Variables
```bash
CHUNK_STRATEGY=progressive  # progressive, service, module
MAX_CHUNK_TOKENS=140000     # Conservative token limit
CHUNK_OVERLAP_TOKENS=10000  # Context overlap between chunks
ENABLE_SMART_MERGING=true   # Enable abstraction merging
```

## Technical Considerations

### Token Counting
- Implement accurate token counting for different LLM providers
- Account for prompt template overhead
- Buffer for response tokens

### Memory Management
- Efficient chunk processing to avoid memory bloat
- Streaming processing for very large repositories
- Garbage collection between chunks

### Quality Assurance
- Validation that chunked results match single-pass quality
- Abstraction completeness verification
- Relationship integrity checks

## Future Enhancements

### Advanced Chunking Strategies
- **Semantic Chunking**: Group files by code similarity
- **Dependency-Aware Chunking**: Chunk based on import/dependency graphs
- **User-Guided Chunking**: Allow manual service/module definitions

### Performance Optimizations
- **Parallel Processing**: Process chunks in parallel where possible
- **Caching**: Cache chunk results for incremental updates
- **Streaming**: Stream large file processing

### Multi-Provider Support
- **Provider-Specific Limits**: Handle different token limits per provider
- **Automatic Provider Switching**: Fallback to providers with larger contexts
- **Cost Optimization**: Choose optimal provider for chunk size

## Success Metrics

### Functionality Metrics
- Successfully process repositories > 200K tokens
- Zero failures on token limit errors
- Maintain abstraction quality across chunk sizes

### Performance Metrics
- Processing time vs. repository size
- Token usage efficiency
- Memory usage optimization

### Quality Metrics
- Abstraction completeness (compared to single-pass)
- Relationship accuracy preservation
- Tutorial coherence maintenance

## Conclusion

This enhancement strategy will transform the system from a single-repository-size-limited tool to a scalable solution capable of handling enterprise-scale codebases. The progressive chunking approach ensures graceful degradation while maintaining output quality, making the system robust and user-friendly regardless of repository complexity.

The implementation leverages existing PocketFlow infrastructure (retry mechanisms, shared state, BatchNode patterns) while adding intelligent context management that can adapt to various LLM provider limitations and account tiers.
