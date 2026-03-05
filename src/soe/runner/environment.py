import subprocess
import os
import sys
from typing import Optional
import venv
import logging
import tempfile
from pathlib import Path
import shutil

logging.basicConfig(
		level=logging.INFO,
		format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
		handlers=[
				logging.FileHandler("runtime.log", mode="w"), 
				logging.StreamHandler(sys.stdout)
		]
)

logger = logging.getLogger('environment')


class RunnerEnvironment:
	def __init__(self, project_path: Path):
		self.project_path = Path(project_path).resolve()
		self.environment_path = Path(tempfile.mkdtemp(prefix="python_run_env_"))
		
		# Define executable paths based on OS
		if os.name == 'nt':
			logger.info("OS detected: windows")
			self.python_exe = self.environment_path / "Scripts" / "python.exe"
		else:
			logger.info("OS detected: macOS/Linux")
			self.python_exe = self.environment_path / "bin" / "python"

		self.pip_cmd = [str(self.python_exe), "-m", "pip"]


	def __enter__(self):
		self.init_environment()
		self.install_dependencies()
		return self


	def __exit__(self, exc_type, exc_val, exc_tb):
		# self.cleanup()
		pass


	def init_environment(self):
		"""Creates the virtual environment if it doesn't exist."""
		try:
			logger.info(f"Creating venv at {self.environment_path}")
			# venv.create(self.environment_path, with_pip=True)
			# TODO: set up path to conda
			subprocess.run([
        "conda", "create", "--prefix", str(self.environment_path),
        "python=3.11", "numpy", "pandas", "-y"
    ], check=True)
		except Exception as e:
			logger.error(f"Failed to create environment: {e}")
			raise


	def install_dependencies(self):
		"""Installs dependencies from requirements.txt or pyproject.toml."""
		req_file = self.project_path / "requirements.txt"
		toml_file = self.project_path / "pyproject.toml"

		logger.info("Upgrading pip...")
		subprocess.run([str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)

		if req_file.exists():
			logger.info(f"Installing dependencies from {req_file}")
			subprocess.run(self.pip_cmd + ["install", "-r", str(req_file)], check=True)

		if toml_file.exists():
			logger.info(f"Installing project from {toml_file}")
			subprocess.run(self.pip_cmd + ["install", str(self.project_path)], check=True)


	def run_script(self, script_name: str, args: list = []):
		"""Helper to run a script using the newly created environment."""
		script_path = self.project_path / script_name
		logger.info(f"Running {script_name} with venv...")
		return subprocess.run([str(self.python_exe), str(script_path)] + args)


	def list_modules(self):
		"""Returns a list of all installed modules in the environment."""
		logger.info("Querying installed modules...")
		result = subprocess.run(
			self.pip_cmd + ["list"], 
			capture_output=True, 
			text=True, 
			check=True
		)
		return result.stdout
	

	def cleanup(self):
		"""Removes the virtual environment directory."""
		if self.environment_path.exists():
			logger.info(f"Cleaning up environment at {self.environment_path}")
			shutil.rmtree(self.environment_path)

import sys
import venv
import ensurepip
import os

if __name__ == "__main__":
	# Example usage
	with RunnerEnvironment(project_path=Path("./tests/test_repo")) as env:
		print(env.list_modules())