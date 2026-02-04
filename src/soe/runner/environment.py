import subprocess
import os
import sys
from typing import Optional
import venv
import logging
import tempfile
from pathlib import Path
import shutil

logger = logging.getLogger('environment')

class RunnerEnvironment:
	def __init__(self, project_path: Path, environment_path: Optional[Path] = None):
		self.project_path = Path(project_path).resolve()
		if not environment_path:
			self.is_temporary = True
			self.environment_path = Path(tempfile.mkdtemp(prefix="python_run_env_"))
		else:
			self.is_temporary = False
			self.environment_path = Path(environment_path).resolve()
		
		# Define executable paths based on OS
		if os.name == 'nt':
			logger.info("OS detected: windows")
			self.python_exe = self.environment_path / "Scripts" / "python.exe"
			self.pip_exe = self.environment_path / "Scripts" / "pip.exe"
		else:
			logger.info("OS detected: macOS/Linux")
			self.python_exe = self.environment_path / "bin" / "python"
			self.pip_exe = self.environment_path / "bin" / "pip"

	def __enter__(self):
		self.init_environment()
		self.install_dependencies()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.is_temporary:
			self.cleanup()

	def init_environment(self):
		"""Creates the virtual environment if it doesn't exist."""
		try:
			if not self.python_exe.exists():
				logger.info(f"Creating venv at {self.environment_path}")
				venv.create(self.environment_path, with_pip=True)
			else:
				logger.info("Virtual environment already exists.")
		except Exception as e:
			logger.error(f"Failed to create environment: {e}")
			raise

	def install_dependencies(self):
		"""Installs dependencies from requirements.txt or pyproject.toml."""
		req_file = self.project_path / "requirements.txt"
		toml_file = self.project_path / "pyproject.toml"

		logger.info("Upgrading pip...")
		subprocess.run([str(self.python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)

		print(req_file.resolve())
		if req_file.exists():
			print("a")
			logger.info(f"Installing dependencies from {req_file}")
			subprocess.run([str(self.pip_exe), "install", "-r", str(req_file)], check=True)

		if toml_file.exists():
			logger.info(f"Installing project from {toml_file}")
			# Installs the project in 'editable' mode or standard mode from the project root
			subprocess.run([str(self.pip_exe), "install", str(self.project_path)], check=True)

	def run_script(self, script_name: str, args: list = []):
		"""Helper to run a script using the newly created environment."""
		script_path = self.project_path / script_name
		logger.info(f"Running {script_name} with venv...")
		return subprocess.run([str(self.python_exe), str(script_path)] + args)

	def list_modules(self):
		"""Returns a list of all installed modules in the environment."""
		logger.info("Querying installed modules...")
		result = subprocess.run(
			[str(self.pip_exe), "list"], 
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