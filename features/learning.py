import random
from colorama import Fore, Style

# ── Cheat Sheets ──────────────────────────────────────────────────────────────

CHEAT_SHEETS = {
    'git': [
        ('git init',                   'Create a new local repo'),
        ('git clone <url>',            'Clone remote repo'),
        ('git status',                 'Show working tree status'),
        ('git add .',                  'Stage all changes'),
        ('git commit -m "msg"',        'Commit staged changes'),
        ('git push',                   'Push to remote'),
        ('git pull',                   'Pull latest changes'),
        ('git branch <name>',          'Create new branch'),
        ('git checkout <branch>',      'Switch branch'),
        ('git merge <branch>',         'Merge branch into current'),
        ('git log --oneline',          'Compact commit history'),
        ('git stash',                  'Stash uncommitted changes'),
        ('git stash pop',              'Restore stashed changes'),
        ('git reset --soft HEAD~1',    'Undo last commit, keep changes'),
        ('git rebase -i HEAD~n',       'Interactive rebase last n commits'),
    ],
    'docker': [
        ('docker ps',                  'List running containers'),
        ('docker ps -a',               'List all containers'),
        ('docker images',              'List local images'),
        ('docker run -it <image> sh',  'Run container interactively'),
        ('docker build -t name .',     'Build image from Dockerfile'),
        ('docker stop <id>',           'Stop running container'),
        ('docker rm <id>',             'Remove container'),
        ('docker rmi <image>',         'Remove image'),
        ('docker logs -f <id>',        'Follow container logs'),
        ('docker exec -it <id> sh',    'Shell into running container'),
        ('docker-compose up -d',       'Start services in background'),
        ('docker-compose down',        'Stop and remove services'),
        ('docker system prune',        'Remove unused data'),
    ],
    'pip': [
        ('pip install <pkg>',          'Install a package'),
        ('pip uninstall <pkg>',        'Remove a package'),
        ('pip freeze',                 'List installed packages'),
        ('pip freeze > requirements.txt', 'Export dependencies'),
        ('pip install -r requirements.txt', 'Install from file'),
        ('pip show <pkg>',             'Show package details'),
        ('pip list --outdated',        'Show outdated packages'),
        ('pip install --upgrade <pkg>','Upgrade a package'),
    ],
    'python': [
        ('python -m venv venv',        'Create virtual environment'),
        ('python -m pytest',           'Run tests with pytest'),
        ('python -m http.server 8000', 'Serve files on port 8000'),
        ('python -c "code"',           'Run inline Python code'),
        ('python -m pip install pkg',  'Install pip package'),
        ('python --version',           'Show Python version'),
        ('python -m pdb script.py',    'Debug with pdb'),
    ],
    'npm': [
        ('npm init -y',                'Init package.json'),
        ('npm install',                'Install dependencies'),
        ('npm install <pkg>',          'Install a package'),
        ('npm install -g <pkg>',       'Install globally'),
        ('npm uninstall <pkg>',        'Remove a package'),
        ('npm run <script>',           'Run a script'),
        ('npm test',                   'Run tests'),
        ('npm update',                 'Update packages'),
        ('npm audit',                  'Check for vulnerabilities'),
        ('npx <cmd>',                  'Run package without installing'),
    ],
    'linux': [
        ('ls -la',                     'List files with details'),
        ('cd -',                       'Go to previous directory'),
        ('grep -r "text" .',           'Search recursively'),
        ('find . -name "*.py"',        'Find files by pattern'),
        ('chmod +x script.sh',         'Make file executable'),
        ('ps aux | grep <name>',       'Find process by name'),
        ('kill -9 <pid>',              'Force kill process'),
        ('df -h',                      'Disk usage'),
        ('du -sh *',                   'Dir sizes in current folder'),
        ('tail -f <file>',             'Follow file in real time'),
        ('curl -s url | jq .',         'HTTP request with pretty JSON'),
        ('ssh user@host',              'SSH into server'),
        ('scp file user@host:path',    'Copy file to remote'),
        ('tar -czf out.tar.gz dir',    'Create tar.gz archive'),
        ('tar -xzf file.tar.gz',       'Extract tar.gz'),
    ],
    'powershell': [
        ('Get-Process',                'List running processes'),
        ('Get-ChildItem',              'List directory (like ls)'),
        ('Set-Location <path>',        'Change directory'),
        ('New-Item -ItemType File f',  'Create a file'),
        ('Remove-Item <path>',         'Delete file/dir'),
        ('Get-Content <file>',         'Read file (like cat)'),
        ('Set-Content <file> <text>',  'Write to file'),
        ('Select-String -Path * -Pattern "x"', 'Search in files'),
        ('Get-Service',                'List services'),
        ('Start-Service <name>',       'Start a service'),
        ('Stop-Service <name>',        'Stop a service'),
        ('$var = "value"',             'Set variable'),
        ('Get-History',                'Show command history'),
        ('Invoke-WebRequest <url>',    'HTTP request (like curl)'),
    ],
    'aegis': [
        ('explain <command>',          'AI explains any command before running'),
        ('plan <task>',                'AI plans multi-step task'),
        ('commit-msg',                 'AI generates commit message from staged diff'),
        ('context add <fact>',         'Add context for AI (e.g. "Flask project")'),
        ('new flask-app myapp',        'Scaffold a Flask project'),
        ('ports',                      'List all listening ports'),
        ('kill-port 3000',             'Kill process on port 3000'),
        ('test',                       'Auto-detect and run project tests'),
        ('record start',               'Start recording session'),
        ('record stop',                'Stop and save recording'),
        ('macro record <name>',        'Start recording a macro'),
        ('macro run <name>',           'Replay a macro'),
        ('secret set KEY value',       'Store encrypted secret'),
        ('secret get KEY',             'Retrieve secret'),
        ('theme set dark',             'Switch color theme'),
        ('analytics',                  'Show command usage analytics'),
        ('ssh-add name host user',     'Save SSH profile'),
        ('ssh-connect name',           'Connect via saved profile'),
        ('vars',                       'Show session variables'),
        ('dashboard',                  'Open live system dashboard'),
    ],
}


def show_cheat(topic: str):
    key = topic.lower()
    if key not in CHEAT_SHEETS:
        available = ', '.join(sorted(CHEAT_SHEETS.keys()))
        print(Fore.YELLOW + f'[Aegis] No cheat sheet for "{topic}". Available: {available}' + Style.RESET_ALL)
        return
    sheet = CHEAT_SHEETS[key]
    print(Fore.CYAN + f'\n  Cheat sheet: {topic}' + Style.RESET_ALL)
    print('  ' + '─' * 58)
    for cmd, desc in sheet:
        print(f'  {Fore.GREEN}{cmd:<38}{Style.RESET_ALL} {Fore.WHITE}{desc}{Style.RESET_ALL}')
    print()


# ── "Did you know" tips ───────────────────────────────────────────────────────

TIPS = [
    ('git stash pop',        'Restore your stashed changes with `git stash pop` after switching branches.'),
    ('ctrl+r history',       'Use Ctrl+R inside Aegis to fuzzy-search your command history instantly.'),
    ('explain',              'Type `explain <any command>` to get an AI breakdown before running it.'),
    ('plan',                 'Type `plan set up a React project` and Aegis will plan and run all steps.'),
    ('$VAR = value',         'Set session variables with `$VAR = value` — they expand in subsequent commands.'),
    ('git status',           'Use `git status`, `git log --oneline`, `git diff --staged` to inspect repo state.'),
    ('secret set',           'Store API keys safely: `secret set OPENAI_KEY sk-...` — stored encrypted.'),
    ('ports',                '`ports` shows every listening port and which process owns it.'),
    ('macro record',         'Record a sequence of commands as a macro and replay it with one command.'),
    ('theme set hacker',     'Try `theme set hacker` for a full-green terminal experience.'),
    ('commit-msg',           'Run `commit-msg` after staging your changes — AI writes the commit message.'),
    ('analytics',            '`analytics` shows your most-used commands and success rate over time.'),
    ('context add',          'Tell Aegis your project stack: `context add I am using Flask with PostgreSQL`.'),
    ('cheat docker',         'Forget a Docker command? `cheat docker` prints a full quick-reference card.'),
    ('record start',         'Record your entire session with `record start` — saved to ~/.aegis/recordings/'),
    ('new flask-app',        'Scaffold a full Flask project: `new flask-app my-api` — ready to run instantly.'),
    ('kill-port 3000',       'Something blocking port 3000? `kill-port 3000` finds and kills it.'),
    ('test',                 '`test` auto-detects pytest / jest / go test / cargo test in your project.'),
    ('ls works everywhere',  '`ls` works in Aegis on Windows — translated to `dir` automatically.'),
    ('ssh-add',              'Save SSH servers: `ssh-add prod user@1.2.3.4` then `ssh-connect prod`.'),
]


def get_tip(already_seen: list = None) -> tuple:
    unseen = [t for t in TIPS if t[0] not in (already_seen or [])]
    pool = unseen if unseen else TIPS
    return random.choice(pool)


def show_startup_tip(already_seen: list = None) -> str:
    key, tip = get_tip(already_seen)
    print(Fore.YELLOW + f'  Tip: {tip}' + Style.RESET_ALL)
    return key
