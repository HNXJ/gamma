from core.parser import extract_bash_commands

def test_extract_single_block():
    text = """
    Here is a command:
    ```bash
    ls -la
    ```
    """
    assert extract_bash_commands(text) == ["ls -la"]

def test_extract_multiple_blocks():
    text = """
    ```bash
    ls
    ```
    Intermediate prose.
    ```bash
    cat file.txt
    ```
    """
    assert extract_bash_commands(text) == ["ls", "cat file.txt"]

def test_ignore_comments_and_blank_lines():
    text = """
    ```bash
    ls
    
    # this is a comment
    pwd
    ```
    """
    assert extract_bash_commands(text) == ["ls", "pwd"]

def test_ignore_prose_outside_fences():
    text = "Run `ls -la` to see files."
    assert extract_bash_commands(text) == []
