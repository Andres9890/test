import os, re, glob, urllib.request, json

ACTIONS = [
    'actions/checkout',
    'actions/setup-python',
    'actions/cache',
    'denoland/setup-deno',
    'actions/upload-artifact',
    'BRAINSia/free-disk-space'
]

def get_latest_commit(repo):
    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/releases/latest')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('User-Agent', 'GitHub-Action-Updater')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    token = os.environ.get('GITHUB_TOKEN')
    if token: req.add_header('Authorization', f'token {token}')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            tag_name = data['tag_name']
    except Exception as e:
        print(f'Error fetching release for {repo}: {e}')
        return None, None
        
    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/commits/{tag_name}')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('User-Agent', 'GitHub-Action-Updater')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    if token: req.add_header('Authorization', f'token {token}')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            return data['sha'], tag_name
    except Exception as e:
        print(f'Error fetching commit for {repo}: {e}')
        return None, None

replacements = {}
updated_info = []
for action in ACTIONS:
    sha, tag = get_latest_commit(action)
    if sha and tag:
        tag_str = tag.replace('v', 'v ', 1) if tag.startswith('v') else f'v {tag}'
        pattern = r'(uses:\s*' + re.escape(action) + r')@[^\s#]+(?:\s+#\s*[^\n]+)?'
        replacements[pattern] = f'\g<1>@{sha} # {tag_str}'
        print(f'Latest for {action}: {sha} ({tag})')
        updated_info.append(f"{action} -> {tag} ({sha[:7]})")

files = glob.glob('.github/workflows/*.yml') + glob.glob('.github/workflows/*.yaml')
changed = False
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content
    for pattern, repl in replacements.items():
        new_content = re.sub(pattern, repl, new_content)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')
        changed = True

if 'GITHUB_OUTPUT' in os.environ:
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f'changed={str(changed).lower()}\n')

if changed:
    with open('commit_message.txt', 'w') as f:
        f.write("Automatic update of GitHub Actions to latest commits\n\n")
        f.write("Updated actions:\n")
        for info in updated_info:
            f.write(f"- {info}\n")
