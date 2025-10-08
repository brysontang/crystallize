from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Iterable

REFERENCE_DIR = Path("docs/src/content/docs/reference")
SOURCE_URL = "https://github.com/brysontang/crystallize/blob/main/"


def _walk_modules(package: str) -> Iterable[str]:
    module = importlib.import_module(package)
    yield package
    if not hasattr(module, "__path__"):
        return
    prefix = f"{package}."
    for _, name, _ in pkgutil.walk_packages(module.__path__, prefix):
        if ".tests" in name.split("."):
            continue
        yield name


def _title_from_module(module_name: str) -> str:
    leaf = module_name.split(".")[-1]
    return leaf.replace("_", " ").title()


def main() -> None:
    packages = [
        "crystallize.datasources",
        "crystallize.experiments",
        "crystallize.pipelines",
        "crystallize.plugins",
        "crystallize.utils",
    ]

    modules: list[str] = []
    for package in packages:
        modules.extend(_walk_modules(package))

    ordered_modules = list(dict.fromkeys(modules))

    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    from lazydocs import MarkdownGenerator

    generator = MarkdownGenerator(src_base_url=SOURCE_URL)

    for path in ordered_modules:
        module_name = path.split(".")[-1]
        md_file = REFERENCE_DIR / f"{module_name}.md"
        module = importlib.import_module(path)
        md_content = generator.import2md(module)
        md_content = md_content.lstrip()
        header = f"# <kbd>module</kbd> `{path}`\n"
        if md_content.startswith(header):
            md_content = md_content.replace(header, f"## <kbd>module</kbd> `{path}`\n", 1)
        frontmatter = f"---\ntitle: {_title_from_module(path)}\n---\n\n"
        with open(md_file, "w") as f:
            f.write(frontmatter + md_content)


if __name__ == "__main__":
    main()
