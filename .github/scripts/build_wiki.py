"""Собирает GitHub Wiki из markdown-файлов репозитория (аналог «Publish code as wiki» в Azure DevOps).

- каждый *.md становится страницей вики (имя файла = заголовок, дефисы -> пробелы);
- папки становятся разделами в _Sidebar.md;
- порядок страниц внутри папки задаётся файлом .order (имена без расширения),
  остальные страницы идут по алфавиту.
"""
import pathlib
import shutil
import sys

src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
SKIP = {".git", ".github"}


def ordered(folder: pathlib.Path):
    entries = [p for p in folder.iterdir() if p.name not in SKIP and not p.name.startswith(".")]
    entries = [p for p in entries if p.is_dir() or (p.suffix == ".md" and p.stem.upper() != "README")]
    order_file = folder / ".order"
    order = []
    if order_file.exists():
        order = [l.strip() for l in order_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    rank = {name: i for i, name in enumerate(order)}
    return sorted(entries, key=lambda p: (rank.get(p.stem if p.is_file() else p.name, len(order)), p.name))


def title(name: str) -> str:
    return name.replace("-", " ")


for old in dst.iterdir():
    if old.name != ".git":
        shutil.rmtree(old) if old.is_dir() else old.unlink()

sidebar = ["* [[Home]]"]


def walk(folder: pathlib.Path, depth: int):
    for p in ordered(folder):
        indent = "  " * depth
        if p.is_dir():
            readme = p / "README.md"
            if readme.exists():
                shutil.copy(readme, dst / f"{p.name}.md")
                sidebar.append(f"{indent}* [[{title(p.name)}]]")
            else:
                sidebar.append(f"{indent}* **{title(p.name)}**")
            walk(p, depth + 1)
        else:
            shutil.copy(p, dst / p.name)
            sidebar.append(f"{indent}* [[{title(p.stem)}]]")


walk(src, 0)

home = src / "README.md"
if home.exists():
    shutil.copy(home, dst / "Home.md")
else:
    (dst / "Home.md").write_text("# Документация\n\nСтраницы опубликованы из репозитория `docs`.\n", encoding="utf-8")

for page in dst.glob("*.md"):
    # в вики страницы адресуются без расширения
    text = page.read_text(encoding="utf-8").replace(".md)", ")")
    page.write_text(text, encoding="utf-8")

(dst / "_Sidebar.md").write_text("\n".join(sidebar) + "\n", encoding="utf-8")
print("\n".join(sidebar))
