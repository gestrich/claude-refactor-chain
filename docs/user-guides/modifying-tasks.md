# Modifying Tasks in spec.md

This guide explains how to safely modify, reorder, insert, and delete tasks in your ClaudeStep spec.md files.

## Table of Contents

- [Overview](#overview)
- [Safe Operations](#safe-operations)
- [Task Description Changes](#task-description-changes)
- [Orphaned PRs](#orphaned-prs)
- [Troubleshooting](#troubleshooting)
- [Migration from Index-Based System](#migration-from-index-based-system)

---

## Overview

ClaudeStep uses **hash-based task identification** where each task is identified by an 8-character SHA-256 hash of its description. This allows you to freely reorder, insert, and delete tasks without breaking the connection between PRs and tasks.

**Key Concept**: The task hash is generated from the task description content, not its position in the file.

---

## Safe Operations

### ✅ Reordering Tasks

You can freely reorder tasks in spec.md at any time:

```markdown
<!-- Before -->
- [ ] Task A
- [ ] Task B
- [ ] Task C

<!-- After - No problem! -->
- [ ] Task C
- [ ] Task A
- [ ] Task B
```

**Why this works**: Each task's hash remains the same because the description hasn't changed. Open PRs will still match correctly.

### ✅ Inserting New Tasks

You can insert new tasks anywhere in the list:

```markdown
<!-- Before -->
- [ ] Task A
- [ ] Task C

<!-- After - No problem! -->
- [ ] Task A
- [ ] Task B  ← New task inserted
- [ ] Task C
```

**Why this works**: New tasks get new hashes, and existing tasks keep their original hashes. No conflicts.

### ✅ Deleting Completed Tasks

You can delete tasks that are already completed:

```markdown
<!-- Before -->
- [x] Task A  ← Completed
- [ ] Task B
- [ ] Task C

<!-- After - Safe to delete -->
- [ ] Task B
- [ ] Task C
```

**Why this works**: Completed tasks have no open PRs, so deleting them doesn't affect anything.

### ⚠️ Deleting Uncompleted Tasks

If you delete a task with an open PR:

```markdown
<!-- Before -->
- [ ] Task A  ← Has open PR #123
- [ ] Task B

<!-- After - Creates orphaned PR -->
- [ ] Task B
```

**Result**: PR #123 becomes "orphaned" (references a task that no longer exists). See [Orphaned PRs](#orphaned-prs) below.

---

## Task Description Changes

### ⚠️ Changing Task Descriptions

When you change a task description, you create a **new task** with a **new hash**:

```markdown
<!-- Before -->
- [ ] Add user authentication  ← Hash: 39b1209d, PR #123 open

<!-- After -->
- [ ] Add OAuth authentication  ← Hash: a8f3c2d1 (NEW!)
```

**Result**:
- PR #123 (hash `39b1209d`) becomes orphaned
- ClaudeStep will detect this and warn you
- You must close PR #123 manually
- ClaudeStep will create a new PR for the updated task (hash `a8f3c2d1`)

### Best Practices

**Option 1: No Open PRs** (Safest)
1. Wait until no PR is open for the task
2. Modify the description
3. Merge to main
4. Next workflow run creates PR with new description

**Option 2: Close and Recreate**
1. Modify the description in spec.md
2. Merge to main
3. Close the orphaned PR (ClaudeStep will warn you which ones)
4. Next workflow run creates new PR with updated description

**Option 3: Update PR Title Manually** (Not Recommended)
- You could update the existing PR to match, but this creates inconsistency
- Better to let ClaudeStep manage the lifecycle

---

## Orphaned PRs

### What are Orphaned PRs?

An **orphaned PR** is a pull request whose task:
- Has been deleted from spec.md, OR
- Has had its description changed in spec.md

### How ClaudeStep Detects Orphaned PRs

When you run the workflow, ClaudeStep compares:
- **Current tasks** in spec.md (with their hashes)
- **Open PRs** (with their branch name hashes)

If a PR's hash doesn't match any current task hash, it's orphaned.

### Warning Messages

**Console Output**:
```
⚠️  Warning: Found 2 orphaned PR(s):
  - PR #123 (claude-step-auth-39b1209d) - task hash 39b1209d no longer matches any task
  - PR #125 (claude-step-auth-a8f3c2d1) - task hash a8f3c2d1 no longer matches any task

To resolve:
  1. Review these PRs and verify if they should be closed
  2. Close any PRs for modified/removed tasks
  3. ClaudeStep will automatically create new PRs for current tasks
```

**GitHub Actions Step Summary**:
```markdown
## ⚠️ Orphaned PRs Detected

Found 2 PR(s) for tasks that have been modified or removed:

- [PR #123](https://github.com/owner/repo/pull/123) (`claude-step-auth-39b1209d`) - task hash `39b1209d` no longer matches any task
- [PR #125](https://github.com/owner/repo/pull/125) (`claude-step-auth-a8f3c2d1`) - task hash `a8f3c2d1` no longer matches any task

**To resolve:**
1. Review these PRs and verify if they should be closed
2. Close any PRs for modified/removed tasks
3. ClaudeStep will automatically create new PRs for current tasks
```

### Resolving Orphaned PRs

**Step 1: Review the PR**
- Click the PR link in the warning
- Check if the work is still relevant
- Decide if you want to keep or close it

**Step 2: Close the PR** (if task description changed or task deleted)
- Go to the PR on GitHub
- Click "Close pull request"
- Add a comment: "Task description changed, closing to allow new PR with updated task"

**Step 3: Wait for New PR** (automatic)
- Next workflow run will create a new PR with the current task description
- The new PR will have a different hash

**Step 4: Merge or Continue** (if keeping the PR)
- If the PR is still valid (e.g., task description is close enough), you can merge it
- Mark the task as complete in spec.md to prevent duplicate PRs

---

## Troubleshooting

### Problem: PR created for wrong task

**Cause**: Task was reordered and you expected PRs to stay in order.

**Solution**: PRs are matched by hash, not position. Check the PR branch name to see which task it's for.

**Example**:
```markdown
# spec.md
- [ ] Task C  ← PR might be for this (hash f7c4d3e2)
- [ ] Task A  ← Not this (hash 39b1209d)
- [ ] Task B  ← Not this (hash a8f3c2d1)
```

Check branch name: `claude-step-myproject-f7c4d3e2` → matches Task C.

### Problem: Orphaned PR warning but I didn't change anything

**Cause**: Someone else modified the task description or deleted the task.

**Solution**:
1. Check the git history: `git log -p -- claude-step/*/spec.md`
2. See who changed the task description
3. Discuss with the team if the change was intentional
4. Close the orphaned PR if needed

### Problem: I want to update a task description without closing the PR

**Not Recommended**: This creates inconsistency between the branch name and the task.

**If you must**:
1. Keep the task description minimal and generic
2. Use comments in spec.md to add details (not part of task checkbox)
3. This way you can update details without changing the hash

**Example**:
```markdown
- [ ] Add user authentication

  Details: Use OAuth 2.0 with Google and GitHub providers.
  ← These details can change without affecting the task hash
```

Only the text immediately after `- [ ]` is used for the hash.

### Problem: Hash collision (two tasks with same hash)

**Likelihood**: Extremely rare (~1 in 4 billion with 8-character SHA-256)

**Symptoms**: Two different task descriptions produce the same hash

**Solution**:
1. Make task descriptions more distinct
2. Add a unique word or number to one of them
3. Report to ClaudeStep maintainers if this happens (very unlikely)

---

## Migration from Index-Based System

If you're upgrading from an older version of ClaudeStep that used index-based task identification:

### What Changed

**Old System** (index-based):
- Tasks identified by position: Task 1, Task 2, Task 3
- Branch names: `claude-step-myproject-1`, `claude-step-myproject-2`
- Reordering tasks broke PR tracking

**New System** (hash-based):
- Tasks identified by content hash: `39b1209d`, `a8f3c2d1`, `f7c4d3e2`
- Branch names: `claude-step-myproject-39b1209d`, `claude-step-myproject-a8f3c2d1`
- Reordering tasks doesn't affect PR tracking

### Backward Compatibility

ClaudeStep supports **both formats** during the transition:

- **Old PRs** (index-based branches) continue to work
- **New PRs** (hash-based branches) are created automatically
- No manual migration required

### Natural Migration

As you merge old PRs and create new ones:
1. Old PRs get merged/closed naturally over time
2. New PRs use hash-based format
3. Eventually all PRs will be hash-based

### Forced Migration (Optional)

If you want to migrate all PRs at once:

1. **Close all open ClaudeStep PRs**
2. **Merge spec.md changes to main**
3. **Run workflow** → Creates new PRs with hash-based branches

**Warning**: This discards work in open PRs. Only do this if PRs are not ready to merge yet.

---

## Best Practices Summary

✅ **DO**:
- Reorder tasks freely
- Insert new tasks anywhere
- Delete completed tasks
- Wait for PRs to merge before changing descriptions

⚠️ **AVOID**:
- Changing task descriptions while PR is open (creates orphaned PR)
- Deleting tasks with open PRs (creates orphaned PR)
- Ignoring orphaned PR warnings (close them promptly)

📝 **REMEMBER**:
- Task hash = Hash of description text
- Changing description = New hash = New task
- ClaudeStep will warn you about orphaned PRs
- Close orphaned PRs, ClaudeStep creates new ones automatically

---

## Questions?

- 🐛 [Report Issues](https://github.com/gestrich/claude-step/issues)
- 💬 [Discussions](https://github.com/gestrich/claude-step/discussions)
- 📚 [Architecture Documentation](../architecture/architecture.md#hash-based-task-identification)
