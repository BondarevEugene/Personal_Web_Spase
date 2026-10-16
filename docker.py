from pathlib import Path


class DockerExporter:

    def generate(self, project_path: Path):
        file = project_path / "Dockerfile"
        file.write_text(
            """
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python","server.py"]
""".strip(),
            encoding="utf-8"
        )
