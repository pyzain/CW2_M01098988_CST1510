import os

def generate_structure(root_dir, indent='', exclusions=['.idea', '__pycache__', 'venv', '.git', 'get_structure.py']):
    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)

        # Skip the exclusion list and hidden files/folders (starting with '.')
        if name in exclusions or name.startswith('.'):
            continue

        if os.path.isdir(path):
            print(f"{indent}├─ {name}/")
            generate_structure(path, indent + '│  ', exclusions)
        else:
            # Add file descriptions for context (optional)
            description = ''
            if name == 'main_app.py':
                description = '# Streamlit orchestrator'
            elif name == 'auth_cli.py':
                description = '# Handles password hashing & verification'
            elif name == 'users.txt':
                description = '# Stores username,hashed_password'

            print(f"{indent}├─ {name} {description}")

# Start the generation
print(f"{os.path.basename(os.getcwd())}/")
generate_structure(os.getcwd())