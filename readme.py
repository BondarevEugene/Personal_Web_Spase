from pathlib import Path


class ReadmeExporter:

    def generate(self, project_path: Path):

        file = project_path / "README.md"

        file.write_text(
            "# OMNIFACTORY Project\n",
            encoding="utf-8"
        )
