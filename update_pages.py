#!/usr/bin/env python3
"""
Update GitHub Pages with new fire analysis visualizations.

This script copies HTML files from outputs/ to docs/ for GitHub Pages hosting.
It can update the main index.html or add additional pages.

Usage:
    # Update main page with latest healdsburg map
    python update_pages.py
    
    # Update with a specific output file
    python update_pages.py --source outputs/my_analysis.html
    
    # Add as an additional page (not the main index)
    python update_pages.py --source outputs/region2.html --name region2
    
    # List all current pages
    python update_pages.py --list
"""

import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime


def get_docs_dir():
    """Get the docs directory path."""
    return Path(__file__).parent / "docs"


def get_outputs_dir():
    """Get the outputs directory path."""
    return Path(__file__).parent / "outputs"


def list_pages():
    """List all HTML pages in docs/."""
    docs_dir = get_docs_dir()
    if not docs_dir.exists():
        print("No docs/ directory found.")
        return
    
    html_files = sorted(docs_dir.glob("*.html"))
    if not html_files:
        print("No HTML pages found in docs/")
        return
    
    print("\n📄 GitHub Pages Files:")
    print("=" * 60)
    for file in html_files:
        size_kb = file.stat().st_size / 1024
        print(f"  • {file.name:<30} ({size_kb:.1f} KB)")
    print("=" * 60)
    print(f"\n🌐 Pages will be available at:")
    print(f"   https://YOUR_USERNAME.github.io/fire-behavior-analysis/")
    print()


def update_page(source_file, page_name=None, set_as_index=True):
    """
    Copy an HTML file to docs/ for GitHub Pages.
    
    Args:
        source_file: Path to source HTML file
        page_name: Name for the page (without .html). If None, uses source filename
        set_as_index: If True, also copy to index.html
    """
    docs_dir = get_docs_dir()
    docs_dir.mkdir(exist_ok=True)
    
    source = Path(source_file)
    if not source.exists():
        print(f"❌ Error: Source file not found: {source}")
        return False
    
    # Determine destination filename
    if page_name:
        dest_name = f"{page_name}.html"
    else:
        dest_name = source.name
    
    dest = docs_dir / dest_name
    
    # Copy file
    shutil.copy2(source, dest)
    print(f"✅ Copied {source.name} → docs/{dest_name}")
    
    # Also update index.html if requested
    if set_as_index:
        index_dest = docs_dir / "index.html"
        shutil.copy2(source, index_dest)
        print(f"✅ Updated docs/index.html")
    
    # Update manifest
    update_manifest(dest_name, source)
    
    return True


def update_manifest(page_name, source_file):
    """Update or create a manifest of pages."""
    docs_dir = get_docs_dir()
    manifest_file = docs_dir / "pages.json"
    
    # Load existing manifest
    if manifest_file.exists():
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {"pages": [], "last_updated": None}
    
    # Update or add page entry
    page_entry = {
        "filename": page_name,
        "source": str(source_file),
        "updated": datetime.now().isoformat(),
        "size_kb": round(Path(source_file).stat().st_size / 1024, 1)
    }
    
    # Remove old entry if exists
    manifest["pages"] = [p for p in manifest["pages"] if p["filename"] != page_name]
    manifest["pages"].append(page_entry)
    manifest["last_updated"] = datetime.now().isoformat()
    
    # Save manifest
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"📝 Updated pages manifest")


def create_index_page():
    """Create an index page that lists all available visualizations."""
    docs_dir = get_docs_dir()
    manifest_file = docs_dir / "pages.json"
    
    if not manifest_file.exists():
        print("No manifest found. Add some pages first.")
        return
    
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    # Create a simple index if there are multiple pages
    if len(manifest["pages"]) > 1:
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Fire Behavior Analysis - Visualizations</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #d32f2f; }
        .page-list { list-style: none; padding: 0; }
        .page-item { margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .page-item a { color: #1976d2; text-decoration: none; font-size: 18px; }
        .page-item a:hover { text-decoration: underline; }
        .page-meta { color: #666; font-size: 14px; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🔥 Fire Behavior Analysis</h1>
    <p>Interactive fire behavior visualizations using LANDFIRE data and Rothermel fire spread model.</p>
    <h2>Available Visualizations</h2>
    <ul class="page-list">
"""
        for page in manifest["pages"]:
            updated = datetime.fromisoformat(page["updated"]).strftime("%Y-%m-%d %H:%M")
            html += f"""        <li class="page-item">
            <a href="{page['filename']}">{page['filename']}</a>
            <div class="page-meta">Updated: {updated} | Size: {page['size_kb']} KB</div>
        </li>
"""
        
        html += """    </ul>
    <hr>
    <p><a href="https://github.com/tbryant/fire-behavior-analysis">View on GitHub</a></p>
</body>
</html>
"""
        
        with open(docs_dir / "all.html", 'w') as f:
            f.write(html)
        
        print("✅ Created docs/all.html with page index")


def main():
    parser = argparse.ArgumentParser(
        description="Update GitHub Pages with fire analysis visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--source', '-s',
        help='Source HTML file from outputs/ directory',
        default=None
    )
    
    parser.add_argument(
        '--name', '-n',
        help='Name for the page (without .html extension)',
        default=None
    )
    
    parser.add_argument(
        '--no-index',
        action='store_true',
        help='Do not set as index.html (just add as additional page)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all current pages in docs/'
    )
    
    parser.add_argument(
        '--create-index',
        action='store_true',
        help='Create an index page listing all visualizations'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_pages()
        return
    
    if args.create_index:
        create_index_page()
        return
    
    # Default: update with healdsburg map
    if args.source is None:
        default_source = get_outputs_dir() / "healdsburg_fire_map.html"
        if not default_source.exists():
            print("❌ No source specified and default healdsburg_fire_map.html not found")
            print("\nAvailable output files:")
            for f in sorted(get_outputs_dir().glob("*.html")):
                print(f"  • {f.name}")
            return
        args.source = str(default_source)
    
    # Update the page
    set_as_index = not args.no_index
    success = update_page(args.source, args.name, set_as_index)
    
    if success:
        print("\n✨ GitHub Pages updated!")
        print("\n📋 Next steps:")
        print("  1. git add docs/")
        print("  2. git commit -m 'Update fire analysis visualization'")
        print("  3. git push")
        print("\n🌐 Your page will be live at:")
        print("   https://YOUR_USERNAME.github.io/fire-behavior-analysis/")


if __name__ == "__main__":
    main()
