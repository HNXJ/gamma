import sys
import os
import json
import shutil

sys.path.append('/Users/HN/MLLM/gamma/src')
from gamma_runtime.mailbox import Mailbox
from arena.rules_resolver import RulesResolver

def test_mailbox():
    print("Testing Mailbox...")
    root = "/tmp/test_mail"
    if os.path.exists(root): shutil.rmtree(root)
    os.makedirs(os.path.join(root, 'announcements'))
    os.makedirs(os.path.join(root, 'agents/agent1/inbox'))
    os.makedirs(os.path.join(root, 'agents/agent1/seen'))
    
    mb = Mailbox(root)
    
    # 1. Broadcast
    ann = {"type": "announcement", "title": "Hello", "body": "World", "priority": 1}
    with open(os.path.join(root, 'announcements/ann1.json'), 'w') as f: json.dump(ann, f)
    
    # 2. Private
    priv = {"type": "task", "title": "Secret", "body": "Agent Only", "priority": 2}
    with open(os.path.join(root, 'agents/agent1/inbox/priv1.json'), 'w') as f: json.dump(priv, f)
    
    input_text = mb.build_agent_input("agent1", "game1", "BB", "Task")
    print(input_text)
    
    assert "[TASK] Secret" in input_text
    assert "[ANNOUNCEMENT] Hello" in input_text
    # Check priority: TASK (2) should be above ANNOUNCEMENT (1)
    assert input_text.index("TASK") < input_text.index("ANNOUNCEMENT")
    
    # 3. Marked seen
    assert os.path.exists(os.path.join(root, 'agents/agent1/seen/priv1.json'))
    assert not os.path.exists(os.path.join(root, 'agents/agent1/inbox/priv1.json'))
    
    print("Mailbox tests passed.")

def test_patches():
    print("Testing Patches...")
    root = "/tmp/test_patches"
    if os.path.exists(root): shutil.rmtree(root)
    os.makedirs(root)
    
    rr = RulesResolver(root)
    
    patch1 = {
        "patch_id": "1.0.0.0",
        "changes": {
            "unlocks": [{"threshold": 40, "id": "VIP"}],
            "features": {"gsdr_allowed": True}
        }
    }
    with open(os.path.join(root, '1.0.0.0.json'), 'w') as f: json.dump(patch1, f)
    
    rules = rr.resolve_rules({}, ["1.0.0.0"])
    print(rules)
    assert rules['features']['gsdr_allowed'] == True
    assert rules['unlocks'][0]['id'] == "VIP"
    
    print("Patch tests passed.")

if __name__ == "__main__":
    test_mailbox()
    test_patches()
