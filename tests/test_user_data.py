import json
from pathlib import Path
import subprocess
from string import Template
import unittest


class UserDataTests(unittest.TestCase):
    def test_rendered_script_has_valid_bash_syntax(self) -> None:
        template = Template(Path("src/user_data.sh").read_text())
        rendered = template.safe_substitute(
            volume_id="vol-0123456789abcdef0",
            volume_id_clean="vol0123456789abcdef0",
            volume_name="ollama-volume",
            models="qwen3:8b llama3.2:latest",
            cloudwatch_config=json.dumps({"metrics": {}}),
        )
        subprocess.run(["bash", "-n"], input=rendered, text=True, check=True)


if __name__ == "__main__":
    unittest.main()
