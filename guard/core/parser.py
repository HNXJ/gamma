import re
from typing import List

def extract_bash_commands(text: str) -> List[str]:
    """
    Extracts commands from fenced bash blocks.
    - Only blocks labeled exactly `bash` are parsed.
    - Blank lines and lines starting with `#` are ignored.
    - Each remaining line is treated as a single command.
    """
    # Regex for ```bash ... ``` blocks
    pattern = re.compile(r'```bash\s*\n(.*?)\n\s*```', re.DOTALL)
    matches = pattern.findall(text)
    
    commands = []
    for block in matches:
        lines = block.splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Note: No support for trailing backslash continuations as per requirements
            commands.append(line)
            
    return commands
