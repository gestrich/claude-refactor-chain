# Refactor Loop: Continuous AI-Powered Code Refactoring

## Getting Started

1. **Start locally** - Run Claude Code locally on ~10 examples to get instructions right before automating.

2. **Set up a test repo** - Use a personal/work repo with Objective-C files. Get the default Claude Code GitHub Action running with a manual workflow trigger.

3. **First milestone** - Get a workflow that runs Claude Code and creates a PR. This validates infrastructure: GitHub token permissions, Claude token, action setup.

4. **Lead with a manual PR** - Stage your first PR manually with several example refactors. This kicks off the chain and sets the pattern.

5. **One at a time initially** - Start with one concurrent PR. You'll be editing instructions frequently early on—don't want multiple PRs doing it wrong.

6. **Use immediate trigger first** - Start with merge-triggered runs for faster iteration. Switch to scheduled (daily) once stable.

7. **Scale up** - As confidence grows, increase concurrent PRs and move to scheduled triggers.

## Overview

An automated system for performing ongoing code refactoring using AI (Claude Code) and GitHub Actions. The core idea is to create a "refactor chain" that continuously generates pull requests for incremental refactoring work, reducing the manual burden and maintaining momentum on large-scale codebase improvements.

## Problems Being Solved

1. **Motivation & Inertia** - Large refactors require creating many PRs over time. Having an automated system breaks the inertia and keeps progress moving.

2. **Burden of Review** - By delivering one PR at a time, the review burden becomes manageable.

3. **Tracking Progress** - The system provides visibility into what's done vs. what remains.

4. **Hands-off Operation** - Runs automatically, sending notifications when work is ready for review.

## Folder Structure

```
/refactor
  /<refactor-name>/
    plan.md           # Checklist of items to refactor
    pr-template.md    # Template for PR descriptions
    config.json       # Settings (see Configuration)
```

Instructions can live as Claude Code commands in your `.claude/commands/` directory for long-term reuse.

## Configuration

A `config.json` file per refactor project:

```json
{
  "label": "swift-migration",
  "maxConcurrentPRs": 1,
  "branchFormat": "refactor/swift-migration-{item}"
}
```

- **label** - GitHub tag used to identify PRs for this refactor
- **maxConcurrentPRs** - How many PRs can be open at once (start with 1)
- **branchFormat** - Pattern for branch names

## Trigger Algorithm

1. Query GitHub API for open PRs with the configured label
2. If count < `maxConcurrentPRs`:
   - Read `plan.md`, find next unchecked item
   - Run Claude Code with the refactor instructions
   - Create PR with the configured label
3. If at max, do nothing (wait for merge)

## Trigger Modes

| Mode | How It Works | Best For |
|------|--------------|----------|
| **Scheduled** | Runs daily via cron | Predictable workload, steady pace |
| **Immediate** | Triggers on PR merge (if label matches) | Fast iteration, rapid progress |

Recommendation: Start with immediate trigger for faster feedback, switch to scheduled once the process is stable.

## How It Works

### 1. Define the Plan

Create `plan.md` with a checklist:
```markdown
## Swift Migration Plan

- [ ] Convert UserManager.m
- [ ] Convert NetworkClient.m
- [x] Convert Logger.m (completed)
```

### 2. Create the Specification

Write detailed rules for the refactor:
- Coding patterns to follow
- Before/after examples
- Edge cases
- Can be a Claude Code command for reuse

### 3. The Refactor Chain (GitHub Action)

Runs on schedule or merge trigger:
1. Check for open PRs with the label
2. If under max, create a new PR for the next item
3. Apply the label and use the PR template

### 4. Human Review & Refinement

When notified:
- Review and merge if good
- If issues: fix and **update the instructions in the same PR**
- Goal: incrementally improve toward 90%+ accuracy

## Improving Instructions

- **Add fixes to the same PR** - When you see instruction gaps, add improvements alongside the refactor code. Keeps the process clean.
- **Expect frequent edits early** - This is normal. Instructions will stabilize over time.
- **Start with one PR at a time** - Easier to iterate when you're not fixing multiple PRs with outdated instructions.

## Quality & Review Responsibility

**You are responsible for this code.** AI-generated refactors are no different than using IDE refactor tools—the responsibility stays with you.

### Team Considerations

- **Agree on review levels per refactor type** - Mechanical renames may need less scrutiny than logic changes.
- **Define QA involvement** - Does QA need to test every PR, or can some be batched weekly?
- **CI vs. manual testing** - Is your test coverage sufficient, or do engineers need to build and run locally?

### Make It Part of Your Pipeline

- If QA reviews weekly, batch these PRs for that review
- Don't let refactor PRs become noise—integrate them into your existing process

### PR Template Tips

Include a "Things to Check" section in your PR template with a checklist based on the refactor type.

## Rejecting PRs

Options for handling bad PRs:
- Check out the branch, mark item as skipped in `plan.md`
- (Future/Bonus) Use Claude Code mentions to close or update the PR automatically

## Other Considerations

- **Local Build Script** - Fetch open PRs and build locally on a schedule. Ready to run when you sit down to review.

- **UI Automation Screenshots** - Capture screenshots showing the result. Visual verification without manual testing.

- **Progress Celebration** - Post to Slack on merge: "✅ 47/300 files converted to Swift". Keeps momentum visible.

## Implementation Plan

### Phase 1: Foundation

- [ ] Set up test repo with sample Objective-C files
- [ ] Get Claude Code GitHub Action running with manual trigger
- [ ] Create first PR successfully via workflow
- [ ] Set up GitHub token with PR creation permissions

### Phase 2: Trigger Logic

- [ ] Implement label-based PR detection
- [ ] Build trigger algorithm (check open PRs, create if under max)
- [ ] Add merge-triggered workflow
- [ ] Add scheduled (cron) workflow option

### Phase 3: Structure & Config

- [ ] Create `/refactor` folder structure
- [ ] Build `config.json` schema
- [ ] Create `plan.md` template
- [ ] Create PR template with checklist

### Phase 4: Polish & Launch

- [ ] Add Slack notifications
- [ ] Record video walkthrough
- [ ] Write blog post
- [ ] Open source the repository

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scripting language | Swift | Targeted at iOS developers, config-based so language doesn't limit users |
| CI Platform | GitHub Actions | Widely used, good PR integration |
| AI Tool | Claude Code | Powerful code understanding, follows specifications well |

## Open Questions

- Use custom GitHub Action or out-of-the-box Claude Code action?
- Best approach for Claude token/credential management in Actions?
- How to handle refactors that depend on previous changes?
- Should failed refactors auto-retry or require manual intervention?
- Can Claude Code mentions be used to update/close PRs? (bonus feature)

## Example Use Cases

1. **Objective-C to Swift migration** - Track by file count, convert one file per PR
2. **Dependency injection refactor** - Update classes one at a time to use DI
3. **API modernization** - Update deprecated API calls across the codebase
4. **Test coverage** - Add unit tests to untested files incrementally

## Launch Deliverables

1. **Open source repository** - Complete setup that others can use in their projects
2. **Video walkthrough** - "Chain Refactors" tutorial
3. **Blog post** - Written guide explaining the approach

## Success Metrics

- Time from PR creation to merge (review efficiency)
- Percentage of PRs merged without modification
- Total items completed over time
- Specification refinement iterations needed
