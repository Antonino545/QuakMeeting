import re

with open("ui/dashboard_tabs/settings_tab.py", "r") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    # If this line starts with exactly 4 spaces and 'def', it's a class method
    if line.startswith("    def "):
        # Check if previous line was already @objc.python_method
        if not (idx > 0 and "@objc.python_method" in lines[idx-1]):
            # If it's not init, render, or IBAction
            if not any(x in line for x in ["def init(", "def render("]):
                # If we didn't just see @objc.IBAction
                if not (idx > 0 and "@objc.IBAction" in lines[idx-1]):
                    new_lines.append("    @objc.python_method\n")
    
    # If the line contains @objc.python_method but it's indented with 8 spaces, skip it
    if line.startswith("        @objc.python_method"):
        continue

    # Fix the indentation of the inner functions if they were accidentally modified to 4 spaces
    if line.startswith("    def _on_mac_"):
        line = "        " + line[4:]
        
    new_lines.append(line)

with open("ui/dashboard_tabs/settings_tab.py", "w") as f:
    f.writelines(new_lines)
