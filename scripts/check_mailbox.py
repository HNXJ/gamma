import sys
import os
from pathlib import Path

root = Path('/Users/HN/MLLM/gamma')
sys.path.append(str(root / 'src'))

from gamma_runtime.mailbox import Mailbox

mailbox = Mailbox(os.path.join(root, 'local', 'game001', 'mail'))
# Clear seen to see what would be delivered
seen_path = os.path.join(root, 'local', 'game001', 'mail/agents/v1_gamma_proponent/seen/ann_bootstrap.json')
if os.path.exists(seen_path):
    os.remove(seen_path)

input_text = mailbox.build_agent_input('v1_gamma_proponent', 'game001', 'BB Summary', 'Normal Task')
print(input_text)
