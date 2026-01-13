"""Interactive setup command for ClaudeChain.

Guides users through setting up a repository for ClaudeChain step-by-step.
"""

import subprocess
from pathlib import Path


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt user for yes/no with a default.

    Args:
        question: The question to ask
        default: Default value if user just hits enter

    Returns:
        True for yes, False for no
    """
    suffix = "[Y/n]" if default else "[y/N]"
    response = input(f"{question} {suffix} ").strip().lower()

    if not response:
        return default
    return response in ("y", "yes")


def prompt_input(question: str, default: str = "") -> str:
    """Prompt user for input with optional default.

    Args:
        question: The question to ask
        default: Default value if user just hits enter

    Returns:
        User input or default
    """
    if default:
        response = input(f"{question} [{default}]: ").strip()
        return response if response else default
    else:
        return input(f"{question}: ").strip()


def prompt_menu(title: str, options: list[tuple[str, str]]) -> int:
    """Display a menu and get user selection.

    Args:
        title: Menu title
        options: List of (label, description) tuples

    Returns:
        Selected option index (0-based)
    """
    print(f"\n{title}")
    print("-" * len(title))
    for i, (label, description) in enumerate(options, 1):
        print(f"  {i}. {label}")
        if description:
            print(f"     {description}")
    print()

    while True:
        response = input(f"Select option [1-{len(options)}]: ").strip()
        try:
            choice = int(response)
            if 1 <= choice <= len(options):
                return choice - 1
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(options)}")


def validate_git_repo(repo_path: Path) -> bool:
    """Check if path is a git repository."""
    return (repo_path / ".git").is_dir()


def validate_github_repo(repo_path: Path) -> bool:
    """Check if repo has GitHub remote."""
    git_config = repo_path / ".git" / "config"
    if git_config.exists():
        content = git_config.read_text()
        return "github.com" in content
    return False


def has_claudechain_workflow(repo_path: Path) -> bool:
    """Check if ClaudeChain workflow already exists."""
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.exists():
        return False
    for f in workflows_dir.iterdir():
        if f.suffix in (".yml", ".yaml"):
            content = f.read_text()
            if "gestrich/claude-chain" in content or "claudechain" in content.lower():
                return True
    return False


def get_current_branch(repo_path: Path) -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()
        # "HEAD" is returned in detached HEAD state
        if branch and branch != "HEAD":
            return branch
        return "main"
    except subprocess.CalledProcessError:
        return "main"


def get_workflow_name(repo_path: Path) -> str:
    """Get the ClaudeChain workflow name from the workflow file."""
    workflow_file = repo_path / ".github" / "workflows" / "claudechain.yml"
    if workflow_file.exists():
        content = workflow_file.read_text()
        for line in content.split("\n"):
            if line.startswith("name:"):
                return line.split(":", 1)[1].strip()
    return "ClaudeChain"


def setup_new_repo(repo_path: Path) -> int:
    """Walk through full repository setup.

    Args:
        repo_path: Path to the repository

    Returns:
        0 on success, 1 on failure
    """
    print("\n" + "=" * 50)
    print("Setup Repository")
    print("=" * 50)

    # Step 1: Validate git repo
    print("\nStep 1: Validating repository")
    print("-" * 30)

    if not validate_git_repo(repo_path):
        print(f"Error: {repo_path} is not a git repository.")
        print("Please run 'git init' first or provide a valid git repository path.")
        return 1

    print("  Git repository found")

    if not validate_github_repo(repo_path):
        print("  Warning: No GitHub remote detected.")
        if not prompt_yes_no("  Continue anyway?", default=False):
            return 1
    else:
        print("  GitHub remote detected")

    if has_claudechain_workflow(repo_path):
        print("  ClaudeChain workflow already exists!")
        if not prompt_yes_no("  Continue and overwrite?", default=False):
            print("\nTip: Use 'Add project' to add a new project to your existing setup.")
            return 0

    # Step 2: Create workflow file
    print("\nStep 2: Create GitHub Actions Workflow")
    print("-" * 30)

    if prompt_yes_no("  Create ClaudeChain workflow file? (Recommended)", default=True):
        create_workflow_file(repo_path)
        print("  Created .github/workflows/claudechain.yml")
    else:
        print("  Skipped workflow creation")

    # Step 3: Statistics workflow (optional)
    print("\nStep 3: Statistics Workflow (Optional)")
    print("-" * 30)
    print("  The statistics workflow posts progress reports to Slack.")

    if prompt_yes_no("  Create statistics workflow?", default=False):
        create_statistics_workflow(repo_path)
        print("  Created .github/workflows/claudechain-statistics.yml")
    else:
        print("  Skipped statistics workflow")

    # Step 4: GitHub configuration instructions
    print("\nStep 4: Configure GitHub Settings")
    print("-" * 30)
    print("""
  You'll need to configure these settings in your GitHub repository:

  1. Add secret: CLAUDE_CHAIN_ANTHROPIC_API_KEY
     Settings -> Secrets and variables -> Actions -> New repository secret
     Get your API key from: https://console.anthropic.com

  2. Enable PR creation:
     Settings -> Actions -> General -> Workflow permissions
     Check "Allow GitHub Actions to create and approve pull requests"

  3. (Optional) Add secret: CLAUDE_CHAIN_SLACK_WEBHOOK_URL
     For Slack notifications when PRs are created
""")

    input("  Press Enter when you've completed these steps...")

    # Step 5: Create first project
    print("\nStep 5: Create Your First Project")
    print("-" * 30)

    if prompt_yes_no("  Create a project now? (Recommended)", default=True):
        result = add_project(repo_path)
        if result is None:
            return 1
    else:
        print("  Skipped project creation")
        print("\n  Run 'claudechain setup <repo_path>' again and select 'Add project' when ready.")

    # Done - point to deploy step
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("""
Your ClaudeChain configuration is ready!

Next step: Deploy spec (project)
  Run this command again and select 'Deploy spec (project)' to:
  - Push your changes to GitHub
  - Trigger your first workflow

  Or manually:
  1. Commit and push the generated files to your default branch
  2. Go to GitHub -> Actions and trigger the ClaudeChain workflow
""")

    return 0


def trigger_first_workflow(repo_path: Path, project_name: str | None, base_branch: str | None = None) -> None:
    """Guide user through triggering their first workflow.

    Args:
        repo_path: Path to the repository
        project_name: Name of the project that was created, or None
        base_branch: Base branch for the project, or None to use current branch
    """
    if base_branch is None:
        base_branch = get_current_branch(repo_path)
    workflow_name = get_workflow_name(repo_path)

    print(f"""
  This is the final step! You need to get your changes to GitHub to start
  using ClaudeChain.

  IMPORTANT: The workflow files (.github/workflows/) must be merged to your
  repository's default branch (e.g., 'main') before the workflow can be
  triggered. This is a GitHub Actions requirement.

  You have two options:
""")

    choice = prompt_menu(
        "How do you plan to push your changes?",
        [
            ("Create a Pull Request", "Create a PR against your base branch, then merge it"),
            ("Push directly to base branch", "Push commits directly (triggers workflow automatically after first run)"),
        ]
    )

    if choice == 0:
        # PR flow
        print(f"""
  Great! Here's what to do:

  1. Commit your changes:
     git add .
     git commit -m "Add ClaudeChain configuration"

  2. Push to a new branch:
     git push origin HEAD

  3. Create a Pull Request against your repository's default branch
     (This gets the workflow files onto the default branch)

  4. Merge the PR

  After merging, ClaudeChain will automatically detect the new project
  and create a PR for the first task!
""")
    else:
        # Direct push flow
        print(f"""
  Great! Here's what to do:

  1. Commit your changes:
     git add .
     git commit -m "Add ClaudeChain configuration"

  2. Push to your repository's default branch (e.g., 'main'):
     git push origin {base_branch}

     Note: If '{base_branch}' is not your default branch, you'll need to
     first get the workflow files onto the default branch before triggering.
""")

        if project_name:
            print("""
  Once pushed, you'll need to manually trigger the first workflow run.
  After that, ClaudeChain will auto-trigger on PR merges.
""")
            if prompt_yes_no("  Would you like me to trigger the first workflow for you?", default=True):
                run_first_workflow(repo_path, workflow_name, project_name, base_branch)
            else:
                print(f"""
  No problem! You can trigger it manually:

  1. Go to GitHub -> Actions -> {workflow_name}
  2. Click "Run workflow"
  3. Enter project name: {project_name}
  4. Enter base branch: {base_branch}
  5. Click "Run workflow"

  Or run this command after pushing:
    gh workflow run "{workflow_name}" --ref {base_branch} -f project_name={project_name} -f base_branch={base_branch}
""")
        else:
            print("""
  After pushing, go to GitHub -> Actions and manually trigger the workflow,
  or use 'Add project' to create a project first.
""")

    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("""
After the first workflow run, ClaudeChain will automatically:
  - Create a PR for each task in your spec.md
  - Trigger the next task when you merge a PR
  - Mark tasks as complete in spec.md

Happy automating!
""")


def run_first_workflow(repo_path: Path, workflow_name: str, project_name: str, base_branch: str) -> None:
    """Trigger the first workflow run.

    Args:
        repo_path: Path to the repository
        workflow_name: Name of the workflow to run
        project_name: Name of the project
        base_branch: Base branch for the workflow
    """
    command = [
        "gh", "workflow", "run", workflow_name,
        "--ref", base_branch,
        "-f", f"project_name={project_name}",
        "-f", f"base_branch={base_branch}"
    ]
    command_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in command)

    print(f"""
  I'll run this command:
    {command_str}
""")

    if prompt_yes_no("  Proceed?", default=True):
        print("\n  Running workflow...")
        try:
            result = subprocess.run(
                command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            print("  Workflow triggered successfully!")
            print("\n  Check the Actions tab in GitHub to monitor progress.")
        except subprocess.CalledProcessError as e:
            print(f"  Error triggering workflow: {e.stderr}")
            print(f"\n  You can try running this manually:")
            print(f"    cd {repo_path}")
            print(f"    {command_str}")
        except FileNotFoundError:
            print("  Error: 'gh' CLI not found. Please install GitHub CLI first:")
            print("    https://cli.github.com/")
            print(f"\n  Then run:")
            print(f"    cd {repo_path}")
            print(f"    {command_str}")
    else:
        print("  Skipped. You can run it later with:")
        print(f"    {command_str}")


def add_project(repo_path: Path) -> tuple[str, str] | None:
    """Add a new ClaudeChain project to the repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Tuple of (project_name, base_branch) on success, None on failure
    """
    print("\n" + "=" * 50)
    print("Create New Spec (Project)")
    print("=" * 50)

    # Get project name
    print()
    project_name = prompt_input("Project name (e.g., 'auth-refactor', 'api-cleanup')")
    if not project_name:
        print("Error: Project name is required.")
        return None

    # Sanitize project name
    project_name = project_name.lower().replace(" ", "-")
    project_dir = repo_path / "claude-chain" / project_name

    if project_dir.exists():
        print(f"Error: Project '{project_name}' already exists at {project_dir}")
        return None

    # Base branch
    print()
    base_branch = get_current_branch(repo_path)
    base_branch = prompt_input("Base branch for PRs", default=base_branch)

    # Optional: assignee
    print()
    assignee = ""
    if prompt_yes_no("Assign PRs to a specific GitHub user?", default=False):
        assignee = prompt_input("GitHub username")

    # Create the project
    print()
    print(f"Creating project '{project_name}'...")

    project_dir.mkdir(parents=True, exist_ok=True)

    # Create spec.md with sample tasks
    spec_content = f"""# {project_name.replace('-', ' ').title()}

This project will print statements as defined in the tasks below.
Each task creates a simple script that outputs the specified message.

## Tasks

- [ ] Print "Hello World!"
- [ ] Print "Hello World!!"
- [ ] Print "Hello World!!!"
"""
    (project_dir / "spec.md").write_text(spec_content)
    print(f"  Created {project_dir}/spec.md")

    # Create configuration.yml if assignee or non-default base branch
    config_lines = []
    if base_branch != "main":
        config_lines.append(f"baseBranch: {base_branch}")
    if assignee:
        config_lines.append(f"assignee: {assignee}")

    if config_lines:
        config_content = "\n".join(config_lines) + "\n"
        (project_dir / "configuration.yml").write_text(config_content)
        print(f"  Created {project_dir}/configuration.yml")

    # Always create pr-template.md
    template_content = """## Task

{{TASK_DESCRIPTION}}

## Review Checklist

- [ ] Code follows project conventions
- [ ] Tests pass
- [ ] No unintended changes

---
*Auto-generated by ClaudeChain*
"""
    (project_dir / "pr-template.md").write_text(template_content)
    print(f"  Created {project_dir}/pr-template.md")

    # Create pre-action.sh
    pre_action_content = """#!/bin/bash
# Pre-action script - runs before Claude Code execution
# Add any setup steps here (e.g., install dependencies, generate code)

echo "Pre-action script completed successfully"
"""
    pre_action_file = project_dir / "pre-action.sh"
    pre_action_file.write_text(pre_action_content)
    pre_action_file.chmod(0o755)
    print(f"  Created {project_dir}/pre-action.sh")

    # Create post-action.sh
    post_action_content = """#!/bin/bash
# Post-action script - runs after Claude Code execution
# Add any validation steps here (e.g., run tests, lint code)

echo "Post-action script completed successfully"
"""
    post_action_file = project_dir / "post-action.sh"
    post_action_file.write_text(post_action_content)
    post_action_file.chmod(0o755)
    print(f"  Created {project_dir}/post-action.sh")

    print()
    print(f"Project '{project_name}' created successfully!")
    print(f"Edit {project_dir}/spec.md to customize your tasks.")

    return project_name, base_branch


def create_workflow_file(repo_path: Path) -> None:
    """Create the main ClaudeChain workflow file."""
    workflows_dir = repo_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    workflow_content = """name: ClaudeChain

on:
  workflow_dispatch:
    inputs:
      project_name:
        description: 'Project name (folder under claude-chain/)'
        required: true
        type: string
      base_branch:
        description: 'Base branch for PR'
        required: true
        type: string
        default: 'main'
  pull_request:
    types: [closed]
    paths:
      - 'claude-chain/**'

permissions:
  contents: write
  pull-requests: write
  actions: read

jobs:
  run-claudechain:
    runs-on: ubuntu-latest
    steps:
      - uses: gestrich/claude-chain@main
        with:
          anthropic_api_key: ${{ secrets.CLAUDE_CHAIN_ANTHROPIC_API_KEY }}
          github_token: ${{ github.token }}
          project_name: ${{ github.event.inputs.project_name || '' }}
          default_base_branch: ${{ github.event.inputs.base_branch || 'main' }}
          claude_allowed_tools: 'Read,Write,Edit,Bash(git add:*),Bash(git commit:*)'
          # slack_webhook_url: ${{ secrets.CLAUDE_CHAIN_SLACK_WEBHOOK_URL }}
"""
    (workflows_dir / "claudechain.yml").write_text(workflow_content)


def create_statistics_workflow(repo_path: Path) -> None:
    """Create the statistics workflow file."""
    workflows_dir = repo_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    workflow_content = """name: ClaudeChain Statistics

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:

permissions:
  contents: read
  actions: read
  pull-requests: read

jobs:
  statistics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gestrich/claude-chain/statistics@main
        with:
          workflow_file: 'claudechain.yml'
          github_token: ${{ github.token }}
          days_back: 7
          slack_webhook_url: ${{ secrets.CLAUDE_CHAIN_SLACK_WEBHOOK_URL }}
"""
    (workflows_dir / "claudechain-statistics.yml").write_text(workflow_content)


def deploy_to_github(repo_path: Path) -> int:
    """Guide user through deploying ClaudeChain to GitHub.

    Args:
        repo_path: Path to the repository

    Returns:
        0 on success, 1 on failure
    """
    print("\n" + "=" * 50)
    print("Deploy Spec (Project)")
    print("=" * 50)

    # Check for workflow file
    if not has_claudechain_workflow(repo_path):
        print("""
  Error: No ClaudeChain workflow file found.

  Please run 'Setup repository' first to create the workflow files.
""")
        return 1

    # Find existing projects
    projects_dir = repo_path / "claude-chain"
    projects = []
    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if p.is_dir() and (p / "spec.md").exists():
                projects.append(p.name)

    if not projects:
        print("""
  Warning: No projects found in claude-chain/ directory.

  You can still deploy the workflow files, but you'll need to add a
  project before ClaudeChain can create PRs.
""")
        project_name = None
        base_branch = "main"
    else:
        print(f"\n  Found {len(projects)} project(s): {', '.join(projects)}")

        # Ask which project to trigger
        if len(projects) == 1:
            project_name = projects[0]
            print(f"  Will trigger workflow for: {project_name}")
        else:
            print()
            project_name = prompt_input(
                f"Which project to trigger first? ({', '.join(projects)})",
                default=projects[0]
            )
            if project_name not in projects:
                print(f"  Warning: '{project_name}' not found in projects list")

        # Get base branch from project config or prompt
        config_file = projects_dir / project_name / "configuration.yml"
        base_branch = "main"
        if config_file.exists():
            content = config_file.read_text()
            for line in content.split("\n"):
                if line.startswith("baseBranch:"):
                    base_branch = line.split(":", 1)[1].strip()
                    break

        print()
        base_branch = prompt_input("Base branch for this project", default=base_branch)

    print(f"""
  IMPORTANT: Before ClaudeChain can run, the workflow files must be on your
  repository's default branch (usually 'main').

  Current status:
    - Workflow file: .github/workflows/claudechain.yml
    - Projects: {len(projects)} found
    - Target base branch: {base_branch}
""")

    choice = prompt_menu(
        "How would you like to deploy?",
        [
            ("Create a Pull Request", "Create a PR to merge project files to the base branch"),
            ("Push directly", "Push directly to the base branch (if you have permission)"),
        ]
    )

    workflow_name = get_workflow_name(repo_path)

    if choice == 0:
        # PR flow
        print(f"""
  To deploy via Pull Request:

  1. Commit your changes (if not already committed):
     cd {repo_path}
     git add .
     git commit -m "Add ClaudeChain configuration"

  2. Push to a feature branch:
     git push origin HEAD

  3. Create a Pull Request on GitHub against your base branch ('{base_branch}')
     Note: The base branch is where ClaudeChain will merge its generated PRs.

  4. Merge the Pull Request

  After merging, the workflow will be available to trigger.
""")
        if project_name:
            print(f"""
  Once merged, you can trigger the workflow:
    - Go to GitHub -> Actions -> {workflow_name} -> Run workflow
    - Or run: gh workflow run "{workflow_name}" --ref {base_branch} -f project_name={project_name} -f base_branch={base_branch}
""")

    else:
        # Direct push flow
        print(f"""
  To push directly:

  1. Commit your changes (if not already committed):
     cd {repo_path}
     git add .
     git commit -m "Add ClaudeChain configuration"

  2. Push to the base branch ('{base_branch}'):
     git push origin {base_branch}

  Note: The base branch is where ClaudeChain will merge its generated PRs.
""")

        if project_name:
            print("""
  Once pushed, you can trigger the first workflow run.
""")
            if prompt_yes_no("  Would you like me to trigger the workflow now?", default=True):
                run_first_workflow(repo_path, workflow_name, project_name, base_branch)
            else:
                print(f"""
  You can trigger it later:
    - Go to GitHub -> Actions -> {workflow_name} -> Run workflow
    - Or run: gh workflow run "{workflow_name}" --ref {base_branch} -f project_name={project_name} -f base_branch={base_branch}
""")

    print("\n" + "=" * 50)
    print("Deploy Complete!")
    print("=" * 50)
    print("""
After the first workflow run, ClaudeChain will automatically:
  - Create a PR for each task in your spec.md
  - Trigger the next task when you merge a PR
  - Mark tasks as complete in spec.md

Happy automating!
""")

    return 0


def cmd_setup(repo_path: str) -> int:
    """Run the interactive setup wizard.

    Args:
        repo_path: Path to the repository to set up

    Returns:
        0 on success, 1 on failure
    """
    resolved_path = Path(repo_path).resolve()

    print("ClaudeChain Interactive Setup")
    print("=" * 40)
    print()
    print(f"Repository: {resolved_path}")

    if not resolved_path.exists():
        print(f"\nError: Path does not exist: {resolved_path}")
        return 1

    if not resolved_path.is_dir():
        print(f"\nError: Path is not a directory: {resolved_path}")
        return 1

    # Main menu
    choice = prompt_menu(
        "What would you like to do?",
        [
            ("Setup repository", "Create workflow files and configure GitHub settings"),
            ("Create new spec (project)", "Add a new project with spec.md and supporting files"),
            ("Deploy spec (project)", "Push changes to GitHub and trigger first workflow"),
        ]
    )

    if choice == 0:
        return setup_new_repo(resolved_path)
    elif choice == 1:
        result = add_project(resolved_path)
        if result:
            project_name, base_branch = result
            print("\n" + "=" * 50)
            print("Spec Created!")
            print("=" * 50)
            print(f"""
Project '{project_name}' is ready.

Next step: Deploy spec (project)
  Run this command again and select 'Deploy spec (project)' to push
  your changes and trigger the first workflow.
""")
            return 0
        return 1
    elif choice == 2:
        return deploy_to_github(resolved_path)

    return 0
