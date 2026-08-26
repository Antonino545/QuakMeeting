import ast
import os
import sys

def check_file(path):
    with open(path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except Exception:
            return

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.asname or n.name)
        elif isinstance(node, ast.ImportFrom):
            for n in node.names:
                imports.append(n.asname or n.name)
    
    # Very naive unused check (won't catch all, but will catch obvious ones)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    for imp in imports:
        # if the word only appears once (in the import statement), it's probably unused
        import re
        if len(re.findall(r'\b' + re.escape(imp) + r'\b', content)) == 1:
            if imp != "__annotations__":
                print(f"Possible unused import: {imp} in {path}")

for root, dirs, files in os.walk("."):
    if ".git" in root or "__pycache__" in root: continue
    for f in files:
        if f.endswith(".py"):
            check_file(os.path.join(root, f))
