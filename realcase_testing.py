import glob
import os
import subprocess
import sys

import xarray as xr
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors import CellExecutionError
from git import Repo

import tempfile
import venv

# Configuration
git_repo_path = "./"
notebook_folder_name = "examples"
reference_folder_name = "reference_data"


def get_notebooks_paths(root_dir):
    notebook_paths = []
    for path, dirs, files in os.walk(root_dir):
        for file in files:
            if file.startswith("Example") and file.endswith(".ipynb"):
                notebook_paths.append(os.path.join(path, file))
    return notebook_paths


def run_notebook(notebook_path, output):

    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

    try:
        print(f"Running notebook {notebook_path}")
        ep.preprocess(nb, {'metadata': {'path': output}})
        print(f"Notebook {notebook_path} executed successfully!")
    except CellExecutionError as e:
        msg = f"Error executing the notebook {notebook_path}.\n"
        msg += f'See the following error: {e}\n'
        print(msg)
        raise


def compare_files(local_f, reference_f):

    with xr.open_dataset(local_f) as ds_local, xr.open_dataset(reference_f) as ds_reference:
        comparison_result = ds_local.equals(ds_reference)

    return comparison_result


def get_head_notebooks(repo_path):

    repo = Repo(repo_path)

    head_tree = repo.head.commit.tree
    notebook_paths = [blob.path for blob in head_tree.traverse() if blob.path.startswith("examples") and blob.path.endswith(".ipynb")]
    print(notebook_paths)
    return notebook_paths


def read_file_in_head(repo_path, file_path):

    repo = Repo(repo_path)

    file_blob = repo.head.commit.tree / file_path
    file_content = file_blob.data_stream.read().decode('utf-8')

    return file_content


def download_reference_files(commit_hash, output_directory, temp_folder_name):

    username = "fziegner"
    repo_url = f'https://github.com/{username}/tobac.git'

    repo = Repo.clone_from(repo_url, os.path.join(output_directory, temp_folder_name), no_checkout=True)
    repo.git.checkout(commit_hash)

    return os.path.join(output_directory, temp_folder_name)


def create_reference_data(source_directory, output_folder_name, output_directory, notebook_folder_name):

    reference_list = []
    if not isinstance(source_directory, list):
        notebooks = get_notebooks_paths(os.path.join(source_directory, notebook_folder_name))
    else:
        notebooks = source_directory

    for notebook in notebooks:
        notebook_name = os.path.basename(notebook).split(".")[0]
        os.makedirs(os.path.join(output_directory, output_folder_name, notebook_name))
        run_notebook(notebook, os.path.join(output_directory, output_folder_name, notebook_name))
        reference_list.extend(glob.glob(os.path.join(output_directory, output_folder_name, notebook_name, "Save", "*")))
        break

    return reference_list


def download_tobac(dest_directory, dest_folder, tag="v1.5.1", ):

    repo_url = f'https://github.com/tobac-project/tobac.git'

    repo = Repo.clone_from(repo_url, os.path.join(dest_directory, dest_folder))
    repo.git.checkout(tag)

    return os.path.join(dest_directory, dest_folder)


def create_venv(env_dir):

    venv.create(env_dir, with_pip=True)

    if sys.platform == "win32":
        python_exec = os.path.join(env_dir, 'Scripts', 'python')
        pip_exec = os.path.join(env_dir, 'Scripts', 'pip')
    else:
        python_exec = os.path.join(env_dir, 'bin', 'python')
        pip_exec = os.path.join(env_dir, 'bin', 'pip')

    return python_exec, pip_exec


def install_requirements(pip_exec, project_dir):

    subprocess.run([pip_exec, 'install', '-r', os.path.join(project_dir, 'requirements.txt')], check=True)
    subprocess.run([pip_exec, 'install', project_dir], check=True)


def main(source="HEAD", target="wd", source_commit=True, target_commit=True, source_commit_hash="d3bca1a1dc5e34ec7d69f968e21a2c71520c545b", target_commit_hash="d3bca1a1dc5e34ec7d69f968e21a2c71520c545b"):

    with tempfile.TemporaryDirectory() as tmp:

        if source_commit:
            source_files_location = download_reference_files(source_commit_hash, output_directory=tmp, temp_folder_name="source_temp_repo")
            source_references = create_reference_data(source_files_location, "source_data_references", tmp, "examples")
        elif source == "HEAD":
            source_files_location = get_head_notebooks(git_repo_path)
            source_references = create_reference_data(source_files_location, "source_data_references", tmp, "examples")
        else:
            source_references = create_reference_data(git_repo_path, "source_data_references", tmp, "examples")

        if target_commit:
            target_files_location = download_reference_files(target_commit_hash, output_directory=tmp, temp_folder_name="target_temp_repo")
            target_references = create_reference_data(target_files_location, "target_data_references", tmp, "examples")
        elif target == "HEAD":
            target_files_location = get_head_notebooks(git_repo_path)
            target_references = create_reference_data(target_files_location, "target_data_references", tmp, "examples")
        else:
            target_references = create_reference_data(git_repo_path, "target_data_references", tmp, "examples")

        for source_reference in source_references:
            target_reference = source_reference.replace("source_data_references", "target_data_references")
            if os.path.exists(target_reference):
                result = compare_files(source_reference, target_reference)
                print(f"Comparison result for {source_reference} and {target_reference}: {'Same' if result else 'Different'}")


if __name__ == "__main__":
    main()
