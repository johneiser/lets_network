"""
Generate a json map of modules for use with jstree.

Usage: python3 map.py > map.json
"""
import os, json, lets, importlib

MODULE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "lets",
)

def generate():
    """Generate map of modules."""
    base = MODULE_BASE

    # Walk base directory
    for root, dirs, files in os.walk(base):
        [_,_,path] = root.partition(base + os.path.sep)

        # Yield folder
        if path:
            [parent,_,folder] = path.rpartition(os.path.sep)
            if not parent.startswith("_") and not folder.startswith("_"):
                yield {
                    "id" : path,
                    "parent" : parent or "#",
                    "text" : folder,
                    "type" : "default",
                }

        # Yield modules
        for file in files:
            [name,_,ext] = file.rpartition(os.path.extsep)
            module = os.path.join("lets", path, name)
            if not name.startswith("_"):
                try:
                    mod = importlib.import_module(module.replace(os.path.sep, os.path.extsep))
                    yield  {
                        "id" : module + "_",
                        "parent" : path or "#",
                        "text" : name,
                        "type" : "module",
                        "help" : mod.help(),
                        }
                except ImportError as e:
                    pass

def main():
    """Output map of modules."""
    print(json.dumps(
        sorted(list(
            generate()), key=lambda obj:obj['id']
        )
    ))

if __name__ == "__main__":
    main()
