import re

with open('ui/banner/qt_banner.py', 'r') as f:
    content = f.read()

# I will replace "💤 15m" with "⏭️ Skip" and map the snooze logic to mark_arrived.
content = content.replace('"💤 15m"', '"⏭️ Skip"')
content = content.replace('self.controller.trigger_snooze(900)', 'self.controller.trigger_arrived()')

with open('ui/banner/qt_banner.py', 'w') as f:
    f.write(content)
