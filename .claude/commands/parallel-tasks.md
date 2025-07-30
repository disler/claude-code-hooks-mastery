# Parallel Task Execution

Execute multiple Taskmaster tasks in parallel with intelligent dependency resolution, contextual implementation, and automated git workflow.

## Usage

```
/parallel-tasks 1.2,1.3,1.4 [--dry-run]
```

## Arguments

- **Task IDs**: Comma-separated list of Taskmaster task IDs (e.g., `1.2,1.3,2.1`)
- **--dry-run**: Show execution plan without executing (optional, place at end)

## Implementation

Execute the following comprehensive workflow:

### Phase 1: Planning & Validation
1. **Parse Task IDs**: Validate format and extract task identifiers
2. **Fetch Task Details**: Use Taskmaster to get full task information including descriptions, dependencies, and current status
3. **Dependency Resolution**: 
   - Build complete dependency graph
   - Auto-include any unmet dependencies
   - Notify user of auto-included tasks: "Auto-including dependencies: 1.1, 2.3"
   - Detect circular dependencies and abort if found
4. **Execution Planning**:
   - Group tasks into parallel execution batches (max 4 simultaneous)
   - Respect dependency order within batches
   - Create execution timeline
5. **Dry-run Check**: If `--dry-run` flag present, display execution plan and exit

### Phase 2: Parallel Task Execution
Execute tasks in dependency-respecting parallel batches:

**For each task in batch:**
```
Task(description="Execute Taskmaster task [ID]", 
     prompt="Execute Taskmaster task [ID]: [TASK_TITLE]. Use hybrid contextual approach: 1) Read task details from Taskmaster, 2) Analyze relevant codebase patterns and architecture, 3) Implement following existing conventions, 4) Auto-detect and run tests if needed. Focus on quality implementation that integrates well with existing code.", 
     subagent_type="general-purpose")
```

**Success Criteria per Task:**
- Implementation completed (code written/modified)
- Auto-detected tests pass (if tests exist or were created)
- No syntax/compilation errors

**After each successful task:**
```
Task(description="Commit task changes", 
     prompt="Update git with changes for task [ID]: [TASK_TITLE]", 
     subagent_type="git-flow-automator")
```

### Phase 3: Error Handling & Dependency Impact
**If a task fails:**
1. Mark task as failed
2. Identify all downstream dependent tasks in current batch
3. Skip dependent tasks and mark as "Skipped due to failed dependency [ID]"
4. Continue with independent tasks
5. Alert user: "Task [ID] failed. Skipping dependent tasks: [list]"

### Phase 4: Batch Status Update
**After all parallel execution completes:**
```
Task(description="Update Taskmaster status", 
     prompt="Mark the following tasks as complete in Taskmaster: [successful_task_ids]. Tasks completed successfully with implementations and git commits.", 
     subagent_type="taskmaster-task-updater")
```

### Phase 5: Comprehensive Session Update
**Final step:**
```
Task(description="Update development session", 
     prompt="Update session with detailed parallel task execution results: 
     - Executed tasks: [all_attempted_tasks] 
     - Successful completions: [successful_tasks] 
     - Failed tasks: [failed_tasks] 
     - Skipped due to dependencies: [skipped_tasks]
     - Key implementations: [summary of what was built]
     - Git commits created: [number] 
     - Auto-detected tests run: [test_results]", 
     subagent_type="session-manager")
```

## Execution Strategy

### Parallel Batching Logic
1. **Wave 1**: Execute all tasks with no dependencies (up to 4 parallel)
2. **Wave 2**: Execute tasks whose dependencies completed in Wave 1 (up to 4 parallel)  
3. **Wave N**: Continue until all tasks processed or blocked by failures

### Contextual Implementation Approach
Each general-purpose agent follows the **Hybrid Contextual Strategy**:
- **Project Context**: Analyze existing codebase architecture and patterns
- **Task Focus**: Implement specific task requirements
- **Quality Integration**: Ensure new code follows established conventions
- **Test Awareness**: Auto-detect testing needs and execute when appropriate

### Commit Message Format
Individual commits use hybrid approach:
```
Complete task [ID]: [actual implementation summary]

- [Key changes made]
- [Files modified/created] 
- [Test results if applicable]

Task: [original task title]
```

## Example Usage

```bash
# Execute three tasks in parallel with dependency resolution
/parallel-tasks 2.1,2.3,3.1

# Preview execution plan without running
/parallel-tasks 1.2,1.4,2.2 --dry-run
```

## Expected Output Summary

```
## Parallel Task Execution Complete

**Tasks Processed**: 4 (including 1 auto-included dependency)
**Successful**: 3 tasks completed with commits
**Failed**: 1 task (dependency issues)
**Skipped**: 0 tasks

**Execution Timeline**:
Wave 1: Tasks 1.1, 2.1 (parallel)
Wave 2: Tasks 1.2, 2.3 (parallel, after 1.1 completed)

**Git Commits**: 3 individual commits created
**Session Updated**: Comprehensive progress logged
```

## Error Scenarios

- **Invalid Task IDs**: Abort with clear error message
- **Circular Dependencies**: Abort with dependency chain explanation  
- **Taskmaster Unavailable**: Abort with Taskmaster connection guidance
- **Git Conflicts**: Handle per-task, continue with others
- **Implementation Failures**: Skip dependents, continue with independent tasks

## Notes

- Maximum 4 simultaneous task executions for performance
- True parallelism within dependency constraints
- Comprehensive error handling with downstream impact analysis
- Each task gets individual git commit for traceability
- Session logging includes detailed breakdown of all activities