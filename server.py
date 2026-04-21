import os
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file-organizer")

FILE_MAP = {
    "images": [".jpg", ".jpeg", ".png", ".gif"],
    "pdfs": [".pdf"],
    "docs": [".doc", ".docx"],
    "excels": [".xls", ".xlsx"],
}

def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in FILE_MAP.items():
        if ext in extensions:
            return category
    return "others"


@mcp.tool()
def organize_directory(path: str) -> dict:
    """
    Organize files in a directory into folders by type.
    """
    moved = 0
    skipped = 0

    if not os.path.exists(path):
        return {"error": "Path does not exist"}

    for file in os.listdir(path):
        full_path = os.path.join(path, file)

        # skip directories
        if os.path.isdir(full_path):
            continue

        category = get_category(file)
        target_dir = os.path.join(path, category)

        os.makedirs(target_dir, exist_ok=True)

        try:
            shutil.move(full_path, os.path.join(target_dir, file))
            moved += 1
        except Exception:
            skipped += 1

    return {
        "status": "success",
        "moved": moved,
        "skipped": skipped
    }


if __name__ == "__main__":
    mcp.run()