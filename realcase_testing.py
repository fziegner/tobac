import json
import difflib
import os


def load_notebook(path: str) -> list:
    with open(path, "r", encoding="utf-8") as file:
        notebook = json.load(file)
    filtered_notebook = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    return filtered_notebook


def get_notebooks_paths(root_dir: str) -> dict:
    notebook_paths = {}
    for path, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(path, file)
                notebook_paths[file] = notebook_path
    return notebook_paths


def get_outputs_from_cells(cells: list) -> list[dict]:
    outputs = []
    for cell in cells:
        if cell["cell_type"] == "code":
            cell_outputs = cell.get("outputs", [])
            for output in cell_outputs:
                match = {}
                if 'data' in output and isinstance(output['data'], dict):
                    for key, value in output['data'].items():
                        if (key.startswith('text') and 'html' not in key) or key.startswith('image'):
                            match[key] = value
                else:
                    for key, value in output.items():
                        if (key.startswith('text') and 'html' not in key) or key.startswith('image'):
                            match[key] = value
                if match:
                    outputs.append(match)
    return outputs


def compare_outputs(outputs1: list[dict], outputs2: list[dict], notebook_name: str) -> None:
    diff = difflib.unified_diff(str(outputs1), str(outputs2), fromfile=f"Version1/{notebook_name}", tofile=f"Version2/{notebook_name}")
    has_difference = False
    for line in diff:
        has_difference = True
        print(line)
    if not has_difference:
        print(f"No differences found in outputs of notebook {notebook_name}")


version1_root = "./examples1"
version2_root = "./examples2"

version1_notebooks = get_notebooks_paths(version1_root)
version2_notebooks = get_notebooks_paths(version2_root)

# Iterate through one set of notebooks and find the matching counterpart
for notebook1_name, notebook1_path in version1_notebooks.items():
    notebook2_path = version2_notebooks.get(notebook1_name)

    if notebook2_path is None:
        print(f"Notebook {notebook1_name} does not exist in Version 2")
        continue

    notebook1_cells = load_notebook(notebook1_path)
    notebook2_cells = load_notebook(notebook2_path)

    notebook1_outputs = get_outputs_from_cells(notebook1_cells)
    notebook2_outputs = get_outputs_from_cells(notebook2_cells)

    print(f"Comparing notebook {notebook1_name} outputs")
    compare_outputs(notebook1_outputs, notebook2_outputs, notebook1_name)