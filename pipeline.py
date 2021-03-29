import subprocess
from pathlib import Path

import yaml


class Pipeline:
    def __init__(self, config):
        self.config = config
        self.gitFolder = Path(self.config["gitFolder"])
        self.load_project_config()

    def load_project_config(self):
        """Get the project's MLproject config, conda env file and env name"""
        mlflow_config_file = self.gitFolder / "MLproject"
        with open(mlflow_config_file) as f:
            self.mlflow_config = yaml.load(f.read(), Loader=yaml.FullLoader)

        self.conda_env_file = self.gitFolder / self.mlflow_config["conda_env"]
        with open(self.conda_env_file) as f:
            conda_config = yaml.load(f.read(), Loader=yaml.FullLoader)

        self.conda_env_name = conda_config["name"]

    def pull_changes(self):
        """Pull changes on the configured branch of the managed repo"""
        # We can't use GitPython for this since it leaks resources over time,
        # see https://gitpython.readthedocs.io/en/stable/intro.html#leakage-of-system-resources
        branch = self.config["branch"]
        process = subprocess.Popen(
            f"git pull origin {branch} && git checkout {branch}",
            shell=True,
            cwd=str(self.gitFolder),
        )
        process.wait()
        if process.returncode > 0:
            raise ValueError(f"Git pull returned code {process.returncode}")

    def _run_proc_check_changes_repo(self, filename, since_hash):
        """Starts a check_changes process on the repo with the project's python
        binary and returns the subproces.Popen object"""
        python_bin = Path.home() / f".conda/envs/{self.conda_env_name}/bin/python"
        return subprocess.Popen(
            f"{python_bin} check_changes.py {filename} {since_hash} --repo={str(self.gitFolder)}",
            shell=True,
        )

    def get_changed_entrypoints(self, since_hash):
        """For each entry point listed in the repo's MLproject,
        runs check_changes to see if the file or its dependencies have
        changed."""
        # Run all checks in parallel
        entrypoint_proc_map = {}
        for entrypoint, spec in self.mlflow_config["entry_points"].items():
            # e.g. python path/to/file --arg --arg2
            entry_file = (self.gitFolder / spec["command"].split()[1]).absolute()
            proc = self._run_proc_check_changes_repo(entry_file, since_hash)
            entrypoint_proc_map[entrypoint] = proc

        changed_entrypoints = []
        for entrypoint, proc in entrypoint_proc_map.items():
            proc.wait()
            if proc.returncode == 1:
                changed_entrypoints.append(entrypoint)

        return changed_entrypoints

    def mlflow_run(self, entrypoint):
        mlflow_bin = Path.home() / f".conda/envs/{self.conda_env_name}/bin/mlflow"

        proc = subprocess.Popen(
            f"{mlflow_bin} run {self.gitFolder} -e {entrypoint}", shell=True
        )
        proc.wait()

    def update_conda(self):
        proc = subprocess.Popen(
            f"conda env update -f {self.conda_env_file};", shell=True
        )
        proc.wait()
        if proc.returncode > 0:
            raise ValueError(
                f"Update conda returned an unknown code: {proc.returncode}"
            )

    def update_conda_if_env_changed(self, since_hash):
        """If the conda env file changed, update the env"""
        proc = self._run_proc_check_changes_repo(self.conda_env_file, since_hash)
        proc.wait()
        if proc.returncode == 1:
            self.update_conda()

    def run_pipeline(self, before_hash):
        self.pull_changes()
        self.load_project_config()
        self.update_conda_if_env_changed(since_hash)

        # TODO: if MLproject file itself changed, then run every entrypoint
        # TODO: not really, just load previous MLproject and check with new one
        entrypoints = self.get_changed_entrypoints(before_hash)

        for entrypoint in entrypoints:
            self.mlflow_run(entrypoint)