import os
import shutil
import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file-organizer")

FILE_MAP = {
    "images": [".jpg", ".jpeg", ".png", ".gif"],
    "pdfs": [".pdf"],
    "docs": [".doc", ".docx"],
    "excels": [".xls", ".xlsx"],
}


# ---------------------------
# Utilities
# ---------------------------

def get_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in FILE_MAP.items():
        if ext in extensions:
            return category
    return "others"


def format_size(size_bytes):
    if size_bytes >= 1024 ** 3:
        return f"{size_bytes / (1024 ** 3):.2f} GB"
    elif size_bytes >= 1024 ** 2:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} B"


def scan_directory_recursive(path):
    entries = []
    total_size = 0

    for dirpath, _, filenames in os.walk(path):
        rel_dir = os.path.relpath(dirpath, path)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1

        folder_size = 0

        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(fp)
                folder_size += size
                total_size += size

                entries.append({
                    "name": filename,
                    "relative_path": os.path.relpath(fp, path),
                    "type": "file",
                    "extension": os.path.splitext(filename)[1].lower(),
                    "size_bytes": size,
                    "depth": depth,
                })
            except Exception as e:
                print(f"[ERROR] File read failed: {fp} → {e}", file=sys.stderr)

        if rel_dir != ".":
            entries.append({
                "name": os.path.basename(dirpath),
                "relative_path": rel_dir,
                "type": "folder",
                "extension": "",
                "size_bytes": folder_size,
                "depth": depth,
            })

    return entries, total_size


def format_analysis_text(data: dict) -> str:
    lines = []

    lines.append(f"📁 Path: {data.get('path')}")
    lines.append(f"📦 Total Size: {data.get('total_size_human')}")
    lines.append("")

    if "entries" in data:
        lines.append("📄 Contents:\n")

        for entry in data["entries"]:
            indent = "  " * entry.get("depth", 0)
            size = format_size(entry["size_bytes"])

            if entry["type"] == "file":
                lines.append(f"{indent}- {entry['name']} ({size})")
            else:
                lines.append(f"{indent}📂 {entry['name']} ({size})")

    elif "items" in data:
        lines.append("📄 Contents:\n")

        for item in data["items"]:
            size = format_size(item["size"])

            if item["type"] == "file":
                lines.append(f"- {item['name']} ({size})")
            else:
                lines.append(f"📂 {item['name']} ({size})")

    return "\n".join(lines)


# ---------------------------
# Tools
# ---------------------------

@mcp.tool()
def organize_directory(path: str) -> dict:
    """
    Organize files in a directory into folders by type.
    """
    moved, skipped = 0, 0

    if not os.path.exists(path):
        return {"error": "Path does not exist"}

    for file in os.listdir(path):
        full_path = os.path.join(path, file)

        if os.path.isdir(full_path):
            continue

        category = get_category(file)
        target_dir = os.path.join(path, category)
        os.makedirs(target_dir, exist_ok=True)

        try:
            shutil.move(full_path, os.path.join(target_dir, file))
            moved += 1
        except Exception as e:
            print(f"[ERROR] Move failed: {file} → {e}", file=sys.stderr)
            skipped += 1

    return {"status": "success", "moved": moved, "skipped": skipped}


@mcp.tool()
def analyze_directory(path: str, recursive: bool = False, as_text: bool = True):
    """
    Analyze directory and return structured data or clean text output.
    """
    if not os.path.exists(path):
        return {"error": "Path does not exist"}

    if recursive:
        entries, total_size = scan_directory_recursive(path)

        data = {
            "path": path,
            "total_size_bytes": total_size,
            "total_size_human": format_size(total_size),
            "entries": entries,
        }

        return format_analysis_text(data) if as_text else data

    # Non-recursive
    result = []
    total_size = 0

    for item in os.listdir(path):
        full_path = os.path.join(path, item)

        try:
            if os.path.isfile(full_path):
                size = os.path.getsize(full_path)
                result.append({"name": item, "type": "file", "size": size})
                total_size += size

            elif os.path.isdir(full_path):
                size = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, files in os.walk(full_path)
                    for f in files
                )
                result.append({"name": item, "type": "folder", "size": size})
                total_size += size

        except Exception as e:
            print(f"[ERROR] Scan failed: {item} → {e}", file=sys.stderr)

    data = {
        "path": path,
        "total_size_bytes": total_size,
        "total_size_human": format_size(total_size),
        "items": result,
    }

    return format_analysis_text(data) if as_text else data


# ---------------------------
# Entry point
# ---------------------------

if __name__ == "__main__":
    try:
        print("[INFO] MCP server starting...", file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"[FATAL] Server crashed: {e}", file=sys.stderr)