import os, json
def generate_context_tree(root, depth=4):
    tree = {}
    for root_dir, dirs, files in os.walk(root):
        rel_path = os.path.relpath(root_dir, root)
        if rel_path.count(os.sep) < depth:
            tree[rel_path] = files
    return tree

# Write to canonical context path
with open("computational/gamma/local/run/context_tree.txt", "w") as f:
    json.dump(generate_context_tree("."), f, indent=2)
