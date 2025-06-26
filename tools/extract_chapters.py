import argparse
import os
from ebooklib import epub
from ebooklib import ITEM_DOCUMENT
from lxml import etree
import re

def clean_title(title):
    """Clean and validate a title."""
    if not title:
        return None
    
    title = title.strip()
    
    # Filter out generic titles
    generic_titles = [
        "what you should see",
        "no title found",
        "untitled",
        "chapter",
        "page"
    ]
    
    if title.lower() in generic_titles:
        return None
    
    # If title is too short, it might not be meaningful
    if len(title) < 3:
        return None
    
    return title

def extract_title_from_content(content):
    """Extract title from XHTML content using multiple methods."""
    try:
        tree = etree.fromstring(content)
        
        # Method 1: Try to get the <title> tag
        title_elem = tree.find('.//{http://www.w3.org/1999/xhtml}title')
        if title_elem is not None and title_elem.text:
            title = clean_title(title_elem.text)
            if title:
                return title
        
        # Method 2: Try to get the first meaningful heading
        for tag in ['h1', 'h2', 'h3', 'h4']:
            heading = tree.find(f'.//{{http://www.w3.org/1999/xhtml}}{tag}')
            if heading is not None and heading.text:
                title = clean_title(heading.text)
                if title:
                    return title
        
        # Method 3: Look for any text content that might be a title
        body = tree.find('.//{http://www.w3.org/1999/xhtml}body')
        if body is not None:
            # Get all text nodes and find the first meaningful one
            for elem in body.iter():
                if elem.text and elem.text.strip():
                    text = elem.text.strip()
                    # Skip if it's just whitespace or very short
                    if len(text) > 10 and not text.isdigit():
                        # Check if it looks like a title (not too long, no special chars)
                        if len(text) < 200 and not re.search(r'[<>{}]', text):
                            title = clean_title(text)
                            if title:
                                return title
        
        return None
    except Exception:
        return None

def generate_title_from_filename(filename):
    """Generate a readable title from filename."""
    # Remove extension
    name = os.path.splitext(filename)[0]
    
    # Handle common patterns
    if name.startswith('ch') and name[2:].isdigit():
        return f"Chapter {name[2:]}"
    elif name.startswith('pref'):
        return "Preface"
    elif name == 'cover':
        return "Cover"
    elif name == 'title':
        return "Title Page"
    elif name == 'copyright':
        return "Copyright"
    elif name == 'toc':
        return "Table of Contents"
    elif name == 'index':
        return "Index"
    elif name.endswith('_images'):
        return f"Images for {name[:-7].title()}"
    elif name.startswith('part'):
        return f"Part {name[4:]}"
    elif name.startswith('fm'):
        return "Front Matter"
    elif name.startswith('bm'):
        return "Back Matter"
    else:
        # Capitalize and replace underscores/hyphens
        return name.replace('_', ' ').replace('-', ' ').title()

def print_toc_recursive(toc, level=0):
    """Recursively print table of contents with proper indentation."""
    for item in toc:
        if hasattr(item, 'title') and item.title:
            indent = "  " * level
            print(f"{indent}• {item.title}")
        if hasattr(item, 'href') and item.href:
            print(f"{indent}  (file: {item.href})")
        
        # Handle nested items
        if hasattr(item, 'subitems') and item.subitems:
            print_toc_recursive(item.subitems, level + 1)

def extract_chapter_titles(epub_path):
    if not os.path.exists(epub_path):
         print(f"File not found: {epub_path}")
         return

    try:
        book = epub.read_epub(epub_path)
        
        print(f"\n=== Chapters in '{os.path.basename(epub_path)}' ===\n")
        
        # Method 1: Try to get from Table of Contents (most reliable)
        if hasattr(book, 'toc') and book.toc:
            print("📖 Table of Contents:")
            print_toc_recursive(book.toc)
            print()
        
        # Method 2: Extract from document content with fallbacks
        print("📄 Document Titles (with fallbacks):")
        chapters = []
        
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            filename = item.get_name().lower()
            
            # Skip image files and other non-chapter content
            if (filename.endswith(('.xhtml', '.html')) and 
                not filename.endswith('_images.xhtml') and
                not filename.endswith('_image.xhtml') and
                not filename.endswith('_img.xhtml') and
                not 'image' in filename and
                not 'img' in filename and
                not filename.startswith('fm') and  # front matter
                not filename.startswith('bm') and  # back matter
                not filename in ['nav.xhtml', 'toc.xhtml', 'index.xhtml']):
                
                content = item.get_content()
                title = extract_title_from_content(content)
                
                if not title:
                    # Fallback: generate title from filename
                    title = generate_title_from_filename(item.get_name())
                
                chapters.append((item.get_name(), title))
        
        if chapters:
            for idx, (filename, title) in enumerate(chapters, 1):
                print(f"{idx:3d}. {title}")
                print(f"      📁 {filename}")
                print()
        else:
            print("No chapters found in this EPUB")
    
    except Exception as e:
        print(f"Failed to read EPUB: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract chapter titles from an EPUB file"
    )
    parser.add_argument(
        "epub_file", help="Path to the EPUB file (e.g. book.epub)"
    )

    args = parser.parse_args()
    extract_chapter_titles(args.epub_file)

if __name__ == "__main__":
    main()
        