import argparse
import glob
import os
import subprocess
import tempfile

import xarray as xr
from git import Repo

parser = argparse.ArgumentParser()
parser.add_argument("--nb", type=str)
parser.add_argument("--c1", type=str)
parser.add_argument("--c2", type=str)
parser.add_argument("--sv", type=str)
parser.add_argument("--c", type=bool)
args = parser.parse_args()


def download_tobac(dest_directory, dest_folder, tag="v1.5.1"):

    repo_url = f'https://github.com/tobac-project/tobac.git'

    repo = Repo.clone_from(repo_url, os.path.join(dest_directory, dest_folder))
    repo.git.checkout(tag)

    return os.path.join(dest_directory, dest_folder)


def create_environment(environment_directory, tobac_version):

    if tobac_version.startswith("v"):
        tobac_version = tobac_version[1::]
    subprocess.run(["mamba", "create", "-y", "-p", environment_directory, "python"], shell=True, check=True)
    subprocess.run(["mamba", "install", "-y", "-c", "conda-forge", "-p", environment_directory, f"tobac={tobac_version}", "jupyter", "arm_pyart", "pytables", "ffmpeg", "gitpython", "nbformat", "nbconvert"], shell=True, check=True)
    #try:
    #    subprocess.run(["mamba", "install", "-y", "-c", "conda-forge", "-p", environment_directory, "--file", os.path.join(tobac_directory, 'requirements.txt')], check=True)
    #except:
    #    subprocess.run(["mamba", "install", "-y", "-c", "conda-forge", "-p", environment_directory, "--file", os.path.join(tobac_directory, 'conda-requirements.txt')], check=True)


def get_reference_file_paths(root_dir):

    file_paths = []

    for dir_path, dir_names, file_names in os.walk(root_dir):
        for dir_name in [d for d in dir_names if d.startswith("Example")]:
            example_folder_path = os.path.join(dir_path, dir_name)
            file_paths.extend(glob.glob(os.path.join(example_folder_path, "Save", "*")))
    return file_paths


def compare_files(reference_file1, reference_file2):

    with xr.open_dataset(reference_file1) as ds_local, xr.open_dataset(reference_file2) as ds_reference:
        comparison_result = ds_local.equals(ds_reference)

    return comparison_result


def compare_files_detailed(reference_file1, reference_file2):

    with open("comparison_results.txt", "a+") as f:
        with xr.open_dataset(reference_file1) as ds_source, xr.open_dataset(reference_file2) as ds_target:
            if ds_source.equals(ds_target):
                print(f"Comparison result for {reference_file1} and {reference_file2}: Same")
                f.write(f"Comparison result for {reference_file1} and {reference_file2}: Same\n")
            else:
                print(f"Comparison result for {reference_file1} and {reference_file2}: Different")
                f.write(f"Comparison result for {reference_file1} and {reference_file2}: Different\n")
                for attribute in set(ds_source.attrs).union(ds_target.attrs):
                    if attribute not in ds_source.attrs or attribute not in ds_target.attrs or ds_source.attrs[attribute] != ds_target.attrs[attribute]:
                        print(f"Global attribute '{attribute}' differs.")
                        f.write(f"Global attribute '{attribute}' differs.\n")

                for variable in set(ds_source.variables).union(ds_target.variables):
                    if variable not in ds_source.variables or variable not in ds_target.variables:
                        print(f"Variable '{variable}' is not present in both files.")
                        f.write(f"Variable '{variable}' is not present in both files.\n")
                    else:
                        for attribute in set(ds_source[variable].attrs).union(ds_target[variable].attrs):
                            if attribute not in ds_source[variable].attrs or attribute not in ds_target[variable].attrs or ds_source[variable].attrs[attribute] != ds_target[variable].attrs[attribute]:
                                print(f"Attribute '{attribute}' of variable '{variable}' differs.")
                                f.write(f"Attribute '{attribute}' of variable '{variable}' differs.\n")

                        if not ds_source[variable].equals(ds_target[variable]):
                            print(f"Data of variable '{variable}' differs.")
                            f.write(f"Data of variable '{variable}' differs.\n")


def main():

    environment_name = "realcase_testing"

    with tempfile.TemporaryDirectory() as tmp:

        if args.sv == "tmp":
            save_directory = tmp
        else:
            save_directory = args.sv
        environment_path = os.path.join(save_directory, environment_name)

        tobac_version = args.c1
        if tobac_version.startswith("v"):
            tobac_version = tobac_version[1::]

        if args.c:
            create_environment(environment_path, tobac_version)
        else:
            subprocess.run(
                ["mamba", "install", "-y", "-c", "conda-forge", "-p", environment_path, f"tobac={tobac_version}"], shell=True, check=True)
        subprocess.run(["mamba", "run", "-p", environment_path, "python", "create_references.py", "--nb", args.nb, save_directory, "source_reference_data"], shell=True, check=True)
        source_paths = get_reference_file_paths(os.path.join(save_directory, "source_reference_data"))

        tobac_version = args.c2
        if tobac_version.startswith("v"):
            tobac_version = tobac_version[1::]
        #environment_path = os.path.join(save_directory, environment_name

        subprocess.run(["mamba", "install", "-y", "-c", "conda-forge", "-p", environment_path, f"tobac={tobac_version}"], shell=True, check=True)
        subprocess.run(["mamba", "run", "-p", environment_path, "python", "create_references.py", "--nb", args.nb, save_directory, "target_reference_data"], shell=True, check=True)

        for source_path in source_paths:
            target_path = source_path.replace("source_reference_data", "target_reference_data")
            if os.path.exists(target_path):
                result = compare_files(source_path, target_path)
                print(f"Comparison result for {source_path} and {target_path}: {'Same' if result else 'Different'}")
                if not result:
                    compare_files_detailed(source_path, target_path)


#  python .\realcase_testing.py --nb v1.5.2 --c1 v1.5.2 --c2 v1.5.1 --sv "./testing" --c False
if __name__ == "__main__":
    main()
