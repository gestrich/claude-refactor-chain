This describes what to manually validate before releases

### Setup

* Go through setup steps on a repo

#### Inital merge

Push a special base branch
Create a project and merge to a base branch
Variations
* Pull request template
* Configuration file
* Model
* Slack webhook
Expect: A pull request is created against the base branch
Expect: Label added
Expect: Slack message posted

### First Auto-generated merge

Expect: Summary to show with costs
Expect: Label added
Expect: Assignee added
Expect: Artifacts Uploaded
Expect: Slack message posted
Merge the PR:
Expect: Another PR to merge

### Statistics

Run statistics workflow
Expect: Slack message posted with costs/open/merged PRs
Expect: Github summary valid

### Manual Worfklow Run

Variations
* base branch (good/bad)
* project name (good/bad)
