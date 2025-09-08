# Roadmap: Incremental Documentation Updates for Pull Requests

## Executive Summary

This roadmap outlines a comprehensive implementation plan to add incremental documentation update capabilities to the AI Codebase Knowledge Builder. The solution will enable cost-effective documentation updates by analyzing only pull request changes rather than regenerating entire documentation sets.

**Expected Impact:**
- 🔥 **Cost Reduction**: 70-90% reduction in LLM usage costs for updates
- ⚡ **Speed Improvement**: 5-10x faster update cycles
- 🎯 **Precision**: Updates only affected documentation sections
- 🔄 **Continuous Integration**: Seamless PR-based workflow integration

---

## 1. Problem Analysis

### Current Limitations
- **Full Regeneration**: Every update processes the entire codebase from scratch
- **High LLM Costs**: Complete analysis requires multiple expensive LLM calls
- **Processing Time**: Full pipeline takes significant time for large repositories
- **No Change Tracking**: Cannot identify which abstractions are affected by specific changes
- **PR Integration Gap**: No support for pull request-specific analysis

### Cost Impact Examples
For a medium-sized repository (100 files, 10 abstractions):
- **Current**: ~50 LLM calls per full regeneration
- **With Incremental**: ~5-15 LLM calls per typical PR update
- **Savings**: 70-90% cost reduction for ongoing maintenance

---

## 2. Solution Architecture

### High-Level Approach

Transform the current **full-regeneration** pipeline into a **smart incremental** system that:

1. **Detects Changes**: Analyzes PR diffs to identify modified files
2. **Maps Impact**: Determines which abstractions are affected by changes
3. **Selective Processing**: Updates only impacted documentation sections
4. **Preserves Context**: Maintains relationships and cross-references
5. **Validates Consistency**: Ensures updated docs remain coherent

### Design Patterns Applied

- **Agent Pattern**: Decision-making nodes determine update scope
- **Differential Processing**: Compare current vs. previous state
- **Selective Batch**: Process only affected abstractions
- **State Management**: Track changes and maintain consistency

---

## 3. Technical Implementation

### 3.1 Enhanced Data Structures

#### Extended Shared Store
```python
shared = {
    # --- Existing Structure (unchanged) ---
    "repo_url": None,
    "files": [],
    "abstractions": [],
    "relationships": {},
    "chapters": [],
    
    # --- NEW: Incremental Update Support ---
    "update_mode": "full" | "incremental",  # Processing mode
    "pr_number": None,  # PR number for GitHub API
    "pr_changes": {  # PR-specific change analysis
        "added_files": [],     # List of newly added files
        "modified_files": [],  # List of changed files
        "deleted_files": [],   # List of removed files
        "diff_content": {}     # File-level diffs
    },
    
    # --- NEW: State Management ---
    "previous_state": {  # Previous documentation state
        "abstractions": [],      # Last known abstractions
        "relationships": {},     # Last known relationships
        "file_hashes": {},      # File content checksums
        "last_commit": None,    # Last processed commit SHA
    },
    
    # --- NEW: Impact Analysis ---
    "impact_analysis": {
        "affected_abstractions": [],  # Abstraction indices needing updates
        "affected_relationships": [], # Relationship changes
        "scope_estimate": None,       # Processing scope (low/medium/high)
        "update_strategy": None,      # Strategy decision
    },
    
    # --- NEW: Caching & Persistence ---
    "cache_dir": ".ai_docs_cache",   # Local cache directory
    "state_file": "doc_state.json", # Persistent state storage
}
```

### 3.2 New Node Implementations

#### 1. `AnalyzePR` Node
```python
class AnalyzePR(Node):
    """Fetches and analyzes pull request changes"""
    
    def prep(self, shared):
        return {
            "repo_url": shared["repo_url"],
            "pr_number": shared["pr_number"],
            "github_token": shared["github_token"],
            "base_branch": shared.get("base_branch", "main")
        }
    
    def exec(self, prep_res):
        # Fetch PR details via GitHub API
        # Get file diffs and change statistics
        # Analyze change patterns and scope
        return pr_changes_data
    
    def post(self, shared, prep_res, exec_res):
        shared["pr_changes"] = exec_res
        shared["update_mode"] = "incremental"
```

#### 2. `LoadPreviousState` Node
```python
class LoadPreviousState(Node):
    """Loads cached documentation state from previous runs"""
    
    def prep(self, shared):
        cache_path = os.path.join(shared["cache_dir"], shared["state_file"])
        return cache_path
    
    def exec(self, cache_path):
        # Load previous abstractions, relationships, file hashes
        # Validate state consistency
        # Handle cache corruption/missing files
        return previous_state_data
    
    def post(self, shared, prep_res, exec_res):
        shared["previous_state"] = exec_res
```

#### 3. `AnalyzeImpact` Node (Agent Pattern)
```python
class AnalyzeImpact(Node):
    """Intelligent analysis of which abstractions need updates"""
    
    def prep(self, shared):
        return {
            "pr_changes": shared["pr_changes"],
            "previous_abstractions": shared["previous_state"]["abstractions"],
            "file_to_abstraction_map": self._build_file_mapping(shared),
            "change_patterns": self._analyze_change_patterns(shared)
        }
    
    def exec(self, prep_res):
        # Use LLM to analyze change impact
        # Determine affected abstractions
        # Estimate update scope and strategy
        prompt = f"""
        Analyze the impact of these code changes on documentation:
        
        Changed files: {prep_res['pr_changes']['modified_files']}
        Current abstractions: {prep_res['previous_abstractions']}
        
        Determine:
        1. Which abstractions are directly affected
        2. Which relationships might have changed
        3. Recommended update strategy (selective/full)
        4. Estimated processing scope (low/medium/high)
        
        Output in YAML format:
        ```yaml
        affected_abstractions: [0, 2, 5]  # indices
        affected_relationships: [...]
        scope_estimate: "medium"
        update_strategy: "selective"
        reasoning: "..."
        ```
        """
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # Parse and validate LLM response
        impact_data = yaml.safe_load(exec_res.split("```yaml")[1].split("```")[0])
        shared["impact_analysis"] = impact_data
        
        # Decision point for routing
        if impact_data["scope_estimate"] == "high":
            return "full_regeneration"
        else:
            return "selective_update"
```

#### 4. `SelectiveUpdateAbstractions` Node
```python
class SelectiveUpdateAbstractions(Node):
    """Updates only affected abstractions using changed files"""
    
    def prep(self, shared):
        affected_indices = shared["impact_analysis"]["affected_abstractions"]
        changed_files = shared["pr_changes"]["modified_files"]
        
        # Get content for affected files only
        affected_content = self._get_affected_content(shared, changed_files)
        
        return {
            "affected_indices": affected_indices,
            "affected_content": affected_content,
            "previous_abstractions": shared["previous_state"]["abstractions"],
            "language": shared["language"]
        }
    
    def exec(self, prep_res):
        # Update only affected abstractions using LLM
        # Preserve existing abstractions that weren't changed
        prompt = f"""
        Update the affected abstractions based on code changes:
        
        Previous abstractions: {prep_res['previous_abstractions']}
        Affected indices: {prep_res['affected_indices']}
        Changed code: {prep_res['affected_content']}
        
        Update only the affected abstractions while preserving others.
        """
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        # Merge updated abstractions with unchanged ones
        updated_abstractions = self._merge_abstractions(
            shared["previous_state"]["abstractions"],
            exec_res,
            prep_res["affected_indices"]
        )
        shared["abstractions"] = updated_abstractions
```

#### 5. `SelectiveUpdateChapters` BatchNode
```python
class SelectiveUpdateChapters(BatchNode):
    """Updates only chapters for affected abstractions"""
    
    def prep(self, shared):
        affected_indices = shared["impact_analysis"]["affected_abstractions"]
        # Return only affected abstraction indices for processing
        return affected_indices
    
    def exec(self, abstraction_index):
        # Generate updated chapter content for this abstraction only
        # Reuse context from unchanged chapters
        return updated_chapter_content
    
    def post(self, shared, prep_res, exec_res_list):
        # Merge updated chapters with existing ones
        shared["chapters"] = self._merge_chapters(
            shared["previous_state"]["chapters"], 
            exec_res_list, 
            prep_res
        )
```

#### 6. `SaveState` Node
```python
class SaveState(Node):
    """Saves current state for future incremental updates"""
    
    def exec(self, prep_res):
        # Generate file hashes for change detection
        # Save abstractions, relationships, chapters
        # Store commit SHA and timestamp
        return state_data
    
    def post(self, shared, prep_res, exec_res):
        # Write state to cache directory
        cache_path = os.path.join(shared["cache_dir"], shared["state_file"])
        self._save_state(cache_path, exec_res)
```

### 3.3 Enhanced Flow Architecture

#### Dual-Mode Flow with Decision Routing
```python
def create_incremental_flow():
    """Creates flow with incremental update capabilities"""
    
    # --- Entry Point: Mode Detection ---
    analyze_pr = AnalyzePR()
    load_state = LoadPreviousState()
    analyze_impact = AnalyzeImpact()
    
    # --- Selective Update Path ---
    selective_abstractions = SelectiveUpdateAbstractions()
    selective_relationships = SelectiveUpdateRelationships()
    selective_chapters = SelectiveUpdateChapters()
    selective_combine = SelectiveCombineTutorial()
    
    # --- Full Regeneration Path (existing nodes) ---
    fetch_repo = FetchRepo()
    identify_abstractions = IdentifyAbstractions()
    # ... existing full pipeline nodes
    
    # --- State Management ---
    save_state = SaveState()
    
    # --- Flow Connections with Branching ---
    analyze_pr >> load_state
    load_state >> analyze_impact
    
    # Decision branching based on impact analysis
    analyze_impact - "selective_update" >> selective_abstractions
    analyze_impact - "full_regeneration" >> fetch_repo
    
    # Selective update path
    selective_abstractions >> selective_relationships >> selective_chapters
    selective_chapters >> selective_combine >> save_state
    
    # Full regeneration path (existing)
    fetch_repo >> identify_abstractions  # ... existing flow
    combine_tutorial >> save_state  # Connect to state saving
    
    return Flow(start=analyze_pr)
```

---

## 4. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Establish basic incremental infrastructure

**Tasks**:
- [ ] Implement enhanced shared store structure
- [ ] Create `AnalyzePR` node for GitHub API integration
- [ ] Implement `LoadPreviousState` and `SaveState` nodes
- [ ] Add state persistence mechanisms (JSON cache files)
- [ ] Create basic file change detection

**Deliverables**:
- Working PR analysis capability
- State persistence framework
- Basic change detection

**Success Criteria**:
- Can fetch and analyze PR changes via GitHub API
- Can save/load documentation state between runs
- Identifies which files changed in a PR

### Phase 2: Impact Analysis (Weeks 3-4)
**Goal**: Smart analysis of change impact on documentation

**Tasks**:
- [ ] Implement `AnalyzeImpact` node with LLM-based analysis
- [ ] Create file-to-abstraction mapping algorithms
- [ ] Develop change pattern recognition
- [ ] Implement decision routing logic (selective vs. full)
- [ ] Add scope estimation capabilities

**Deliverables**:
- Intelligent impact analysis system
- Decision routing framework
- Change scope estimation

**Success Criteria**:
- Accurately identifies affected abstractions from code changes
- Makes intelligent decisions about update scope
- Routes to appropriate processing path

### Phase 3: Selective Updates (Weeks 5-7)
**Goal**: Implement selective update processing

**Tasks**:
- [ ] Create `SelectiveUpdateAbstractions` node
- [ ] Implement `SelectiveUpdateRelationships` node
- [ ] Develop `SelectiveUpdateChapters` BatchNode
- [ ] Build content merging algorithms
- [ ] Add consistency validation

**Deliverables**:
- Complete selective update pipeline
- Content merging framework
- Validation mechanisms

**Success Criteria**:
- Can update only affected documentation sections
- Preserves unchanged content correctly
- Maintains documentation consistency

### Phase 4: Integration & CLI (Weeks 8-9)
**Goal**: Integrate incremental updates with existing CLI

**Tasks**:
- [ ] Extend `main.py` with PR-specific flags
- [ ] Implement dual-mode flow selection
- [ ] Add incremental update command options
- [ ] Create GitHub integration utilities
- [ ] Add comprehensive error handling

**Deliverables**:
- Extended CLI interface
- Complete GitHub integration
- Error handling framework

**Success Criteria**:
- CLI supports both full and incremental modes
- Seamless GitHub PR integration
- Robust error handling and fallbacks

### Phase 5: Optimization & Testing (Weeks 10-12)
**Goal**: Optimize performance and ensure reliability

**Tasks**:
- [ ] Implement advanced caching strategies
- [ ] Add performance monitoring and metrics
- [ ] Create comprehensive test suite
- [ ] Optimize LLM usage patterns
- [ ] Add documentation and examples

**Deliverables**:
- Performance optimization
- Comprehensive testing
- Documentation and examples

**Success Criteria**:
- Achieves 70%+ cost reduction targets
- Passes all reliability tests
- Complete documentation available

---

## 5. Enhanced CLI Interface

### New Command Structure
```bash
# Full regeneration (existing behavior)
python main.py --repo https://github.com/owner/repo

# Incremental update from specific PR
python main.py --repo https://github.com/owner/repo --pr 123

# Incremental update from local changes
python main.py --dir ./local_repo --incremental

# Force full regeneration even with cache
python main.py --repo https://github.com/owner/repo --force-full

# Cache management
python main.py --clear-cache
python main.py --cache-info
```

### New CLI Arguments
- `--pr NUMBER`: Process specific pull request
- `--incremental`: Enable incremental mode for local directories
- `--force-full`: Force full regeneration ignoring cache
- `--cache-dir PATH`: Custom cache directory location
- `--base-branch BRANCH`: Base branch for PR comparison (default: main)
- `--clear-cache`: Clear documentation cache
- `--cache-info`: Display cache status and statistics

---

## 6. Cost Optimization Strategy

### Expected Savings by Repository Size

| Repository Size | Current LLM Calls | Incremental Calls | Savings |
|----------------|-------------------|-------------------|---------|
| Small (20 files) | ~25 calls | ~3-8 calls | 70-85% |
| Medium (100 files) | ~50 calls | ~5-15 calls | 70-90% |
| Large (500+ files) | ~100+ calls | ~10-25 calls | 75-90% |

### Optimization Techniques

1. **Smart Caching**:
   - Cache LLM responses by content hash
   - Reuse unchanged abstraction analyses
   - Cache relationship mappings

2. **Selective Processing**:
   - Process only changed files
   - Update only affected abstractions
   - Preserve unchanged chapters

3. **Efficient Prompting**:
   - Focused prompts for specific changes
   - Incremental context building
   - Reduced token usage per call

4. **Batch Optimization**:
   - Group related updates
   - Minimize API round trips
   - Parallel processing where possible

---

## 7. Risk Assessment & Mitigation

### High Priority Risks

#### 1. **Consistency Degradation**
- **Risk**: Incremental updates may create inconsistent documentation
- **Mitigation**: 
  - Comprehensive validation nodes
  - Periodic full regeneration
  - Cross-reference checking
  - Rollback capabilities

#### 2. **Complex Change Detection**
- **Risk**: Missing subtle dependencies between abstractions
- **Mitigation**:
  - Conservative impact analysis
  - LLM-based relationship detection
  - Fallback to full regeneration for complex changes

#### 3. **Cache Corruption**
- **Risk**: Corrupted cache leading to incorrect updates
- **Mitigation**:
  - Checksums and validation
  - Graceful degradation to full mode
  - Cache repair mechanisms
  - Regular cache health checks

### Medium Priority Risks

#### 4. **GitHub API Limits**
- **Risk**: Rate limiting during PR analysis
- **Mitigation**:
  - API call optimization
  - Caching of PR data
  - Graceful backoff strategies
  - Alternative Git-based analysis

#### 5. **LLM Hallucination**
- **Risk**: Incorrect impact analysis leading to missed updates
- **Mitigation**:
  - Conservative update strategies
  - Multiple validation passes
  - Human review flags for critical changes

---

## 8. Testing Strategy

### 8.1 Unit Testing
- **Node Testing**: Individual node functionality
- **Utility Testing**: Helper functions and utilities
- **State Management**: Cache operations and persistence
- **API Integration**: GitHub API interactions

### 8.2 Integration Testing
- **Flow Testing**: End-to-end incremental flows
- **State Consistency**: Cross-run state validation
- **Fallback Testing**: Full regeneration fallbacks
- **Error Recovery**: Graceful error handling

### 8.3 Performance Testing
- **Cost Validation**: Actual vs. expected LLM usage
- **Speed Benchmarks**: Processing time comparisons
- **Cache Efficiency**: Hit rates and storage optimization
- **Scalability**: Large repository handling

### 8.4 Real-World Testing
- **Live Repository**: Test on actual project repositories
- **PR Workflows**: Real pull request processing
- **Edge Cases**: Complex change scenarios
- **User Acceptance**: Developer workflow integration

---

## 9. Success Metrics

### Quantitative Goals
- **Cost Reduction**: 70%+ reduction in LLM costs for typical updates
- **Speed Improvement**: 5-10x faster processing for incremental updates
- **Accuracy**: 95%+ correct identification of affected abstractions
- **Cache Hit Rate**: 80%+ reuse of unchanged content

### Qualitative Goals
- **Developer Experience**: Seamless PR-based workflow integration
- **Reliability**: Consistent documentation quality
- **Maintainability**: Clean, extensible codebase
- **Documentation**: Comprehensive usage guides and examples

---

## 10. Future Enhancements

### Advanced Features (Post-MVP)
- **Multi-PR Analysis**: Batch processing multiple PRs
- **Semantic Change Detection**: Advanced code understanding
- **Auto-PR Creation**: Automatic documentation PRs
- **CI/CD Integration**: GitHub Actions workflow
- **Delta Visualization**: Show what changed in docs
- **Approval Workflows**: Human review for critical changes

### Ecosystem Integration
- **GitHub App**: Native GitHub application
- **IDE Plugins**: Editor integrations
- **API Endpoints**: REST API for external tools
- **Webhook Support**: Real-time PR processing

---

## 11. Implementation Resources

### Required Skills
- **Python Development**: Advanced Python programming
- **LLM Integration**: Experience with LLM APIs and prompting
- **GitHub API**: REST API integration
- **Git Operations**: Advanced Git functionality
- **System Design**: Distributed system architecture

### External Dependencies
- **GitHub API**: PR analysis and diff retrieval
- **Git Libraries**: Advanced Git operations (GitPython)
- **Caching Libraries**: Efficient state management
- **Async Libraries**: For performance optimization

### Estimated Effort
- **Total Duration**: 12 weeks
- **Full-Time Developer**: 1 experienced developer
- **Key Milestones**: 5 major phases
- **Testing Overhead**: ~30% of development time

---

## Conclusion

This comprehensive roadmap provides a robust foundation for implementing incremental documentation updates. The phased approach ensures steady progress while maintaining system reliability. The expected 70-90% cost reduction will make the system significantly more practical for ongoing documentation maintenance, enabling continuous documentation updates that keep pace with active development.

The implementation leverages the existing PocketFlow architecture while adding intelligent decision-making capabilities that route updates through the most efficient processing path. This preserves the system's simplicity while dramatically improving its efficiency for real-world usage scenarios.
