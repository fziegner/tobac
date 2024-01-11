import glob
import os
import xarray as xr
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors import CellExecutionError
from git import Repo
import tempfile

# Configuration
git_repo_path = "./"
notebook_folder_name = "examples"
reference_folder_name = "reference_data"


def get_notebooks_paths(root_dir):
    notebook_paths = {}
    for path, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(path, file)
                notebook_paths[file] = notebook_path
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
    return notebook_paths


def read_file_in_head(repo_path, file_path):

    repo = Repo(repo_path)

    file_blob = repo.head.commit.tree / file_path
    file_content = file_blob.data_stream.read().decode('utf-8')

    return file_content


def main(source="wd", target="HEAD"):

    with tempfile.TemporaryDirectory() as tmp:
        if source == "HEAD":
            notebooks = get_head_notebooks(git_repo_path)
        else:
            notebooks = get_notebooks_paths(git_repo_path + notebook_folder_name).values()

        if target == "HEAD":
            notebooks_reference = get_head_notebooks(git_repo_path)

        for nb in notebooks:
            notebook_name = nb.replace("\\", "/").split("/")[-1].split(".")[0]
            os.mkdir(os.path.join(tmp, notebook_name))
            run_notebook(nb, os.path.join(tmp, notebook_name))
            netcdf_files = glob.glob(os.path.join(tmp, notebook_name, "Save", "*"))
            if target == "zenodo":
                reference_folder = git_repo_path + os.path.join(reference_folder_name, notebook_name, "Save")
                for local_file in netcdf_files:
                    reference_file = os.path.join(reference_folder, local_file.rsplit(os.sep, 1)[1])
                    if os.path.exists(reference_file):
                        result = compare_files(local_file, reference_file)
                        print(f"Comparison result for {nb}: {'Same' if result else 'Different'}")
            else:
                for nb_ in notebooks_reference:
                    if notebook_name in nb_:
                        os.makedirs(os.path.join(tmp, notebook_name + "_reference"))
                        run_notebook(nb_, os.path.join(tmp, notebook_name + "_reference"))
                        netcdf_files_reference = glob.glob(os.path.join(tmp, notebook_name + "_reference", "Save", "*"))
                        for local_file, reference_file in zip(netcdf_files, netcdf_files_reference):
                            if os.path.exists(local_file) and os.path.exists(reference_file):
                                result = compare_files(local_file, reference_file)
                                print(f"Comparison result for {nb_}: {'Same' if result else 'Different'}")
                        break


if __name__ == "__main__":
    main()
