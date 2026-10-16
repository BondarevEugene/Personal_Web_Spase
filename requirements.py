from pathlib import Path


class RequirementsExporter:

    def generate(self, project_path: Path):

        file = project_path / "requirements.txt"

        file.write_text(
            "fastapi\nuvicorn\njinja2\n",
            encoding="utf-8"
        )
