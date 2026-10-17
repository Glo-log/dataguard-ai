# Review and GitHub publication

A local initial commit is prepared on **`main`**. No remote repository has been created, no remote is configured, and nothing has been pushed or deployed. **Run the publication steps only after explicit approval.** The intended repository name is **`dataguard-ai`**.

## Review the prepared commit

Run from the project root:

```powershell
$DataGuardRepositoryPath = (Get-Location).Path.Replace('\', '/')
$DataGuardGitOptions = @('-c', "safe.directory=$DataGuardRepositoryPath")
git @DataGuardGitOptions status --short
git @DataGuardGitOptions log -1 --oneline
git @DataGuardGitOptions show --stat HEAD
git @DataGuardGitOptions show --format= --check HEAD
git @DataGuardGitOptions remote -v
git @DataGuardGitOptions check-ignore data/raw/online_retail/online_retail.zip data/processed/online_retail.csv .venv/pyvenv.cfg
.\.venv\Scripts\python.exe -m pytest -q
```

`git status --short` should be empty. `git remote -v` should be empty before publication. Raw/full data, secrets, environments, local audit copies, and generated caches are excluded. The committed samples and images are small; Git LFS is not needed.

The temporary Git options trust only the current project directory for those commands. This addresses the observed ownership difference between the sandbox account that initialized `.git` and the desktop account, without changing global Git settings. They are harmless when ownership already matches.

## Publish using the GitHub website and Git

This route requires Git, which is installed; GitHub CLI is optional and was not found during the audit.

1. After approval, sign in to [GitHub's new repository page](https://github.com/new).
2. Name the repository **`dataguard-ai`**, choose the owner and visibility, and create it **empty**. Do not add a README, `.gitignore`, or license through the website; they are already in the local commit.
3. Run these PowerShell commands from this project directory, entering the owner selected above:

```powershell
$DataGuardRepositoryPath = (Get-Location).Path.Replace('\', '/')
$DataGuardGitOptions = @('-c', "safe.directory=$DataGuardRepositoryPath")
$DataGuardGitHubOwner = Read-Host "GitHub username or organization"
git @DataGuardGitOptions remote add origin "https://github.com/$DataGuardGitHubOwner/dataguard-ai.git"
git @DataGuardGitOptions remote -v
git @DataGuardGitOptions push -u origin main
```

Authenticate through Git Credential Manager or your own GitHub tools if prompted. Do not put a password or token into the URL or repository files. If `origin` already exists, inspect `git remote -v` before changing it; the commands assume the audited state with no remote.

## Verify after publishing

Check the actual repository page, README screenshots, branch, and first GitHub Actions run. Remote CI and Community Cloud have not run during this local audit. Follow `docs/DEPLOYMENT.md` separately if you later approve deployment. No publishing command in this document was executed by the audit.
