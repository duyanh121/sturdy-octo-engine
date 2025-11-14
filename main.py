from src.runner import Runner
from src.generator import StringGenerator

runner = Runner("run/test.py", [StringGenerator])

print(runner.run().stdout)
