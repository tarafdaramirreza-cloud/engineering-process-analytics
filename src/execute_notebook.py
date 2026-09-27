"""Execute the learning notebook with the same interpreter as this command."""

import os
from pathlib import Path
import sys
import tempfile
import nbformat
from nbclient import NotebookClient
from ipykernel.kernelspec import install


def main():
    root = Path(__file__).resolve().parents[1]
    notebook_path = root / "notebooks/01_exploratory_analysis.ipynb"
    # Temporary kernel registration avoids requiring a global Jupyter install.
    with tempfile.TemporaryDirectory() as directory:
        install(prefix=directory, kernel_name="portfolio-python")
        kernels = Path(directory) / "share/jupyter"
        previous_path = os.environ.get("JUPYTER_PATH")
        os.environ["JUPYTER_PATH"] = str(kernels) + (os.pathsep + previous_path if previous_path else "")
        try:
            notebook = nbformat.read(notebook_path, as_version=4)
            client = NotebookClient(notebook, timeout=180, kernel_name="portfolio-python",
                                    resources={"metadata": {"path": str(root)}})
            client.execute()
            nbformat.write(notebook, notebook_path)
        finally:
            if previous_path is None:
                os.environ.pop("JUPYTER_PATH", None)
            else:
                os.environ["JUPYTER_PATH"] = previous_path
    print(f"Executed {notebook_path.name} with {sys.executable}")


if __name__ == "__main__":
    main()
