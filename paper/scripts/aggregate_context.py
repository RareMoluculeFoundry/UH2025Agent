import os
import json
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
SECTIONS_DIR = BASE_DIR / "sections"
REFERENCES_DIR = BASE_DIR / "references"
OUTPUT_FILE = BASE_DIR / "PRESENTATION_CONTEXT.json"

def parse_markdown_section(content, section_header):
    """Extracts content under a specific markdown header until the next header."""
    pattern = re.compile(f"## {section_header}(.*?)(?=## |\Z)", re.DOTALL)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""

def parse_key_value(content, key):
    """Extracts a value for a given key in a list format like '* **Key**: Value'."""
    pattern = re.compile(f"\* \s*\*\*{key}\*\*:\s*(.*)")
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return None

def parse_context_payload(file_path):
    """Parses a CONTEXT_PAYLOAD.md file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # 1. Metadata
    metadata_section = parse_markdown_section(content, "1. Section Metadata")
    section_id = parse_key_value(metadata_section, "ID")
    title = parse_key_value(metadata_section, "Title")
    source_files = parse_key_value(metadata_section, "Source Files")

    # 2. Generative Prompt
    prompt = parse_markdown_section(content, "2. Generative Prompt")

    # 3. Mermaid Diagram
    mermaid_raw = parse_markdown_section(content, "3. Mermaid Diagram Logic")
    # Clean up code blocks
    mermaid_clean = re.sub(r"```mermaid\n", "", mermaid_raw)
    mermaid_clean = re.sub(r"```", "", mermaid_clean).strip()

    # 4. Pull Quotes
    quotes_raw = parse_markdown_section(content, "4. Key Pull-Quotes")
    quotes = [line.strip().lstrip("* ").strip('"') for line in quotes_raw.split("\n") if line.strip().startswith("*")]

    return {
        "section_id": section_id,
        "title": title,
        "source_files": source_files,
        "generative_prompt": prompt,
        "mermaid_diagram": mermaid_clean,
        "pull_quotes": quotes
    }

def get_global_context():
    """Reads the global paper context."""
    context_file = REFERENCES_DIR / "paper_context.md"
    if context_file.exists():
        with open(context_file, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def main():
    print(f"Scanning sections in {SECTIONS_DIR}...")
    
    sections_data = []
    
    # Iterate through numbered sections
    if SECTIONS_DIR.exists():
        section_dirs = sorted([d for d in SECTIONS_DIR.iterdir() if d.is_dir()])
        for section_dir in section_dirs:
            payload_file = section_dir / "CONTEXT_PAYLOAD.md"
            if payload_file.exists():
                print(f"Processing {section_dir.name}...")
                data = parse_context_payload(payload_file)
                if data:
                    sections_data.append(data)
    
    global_context = get_global_context()
    
    final_payload = {
        "project_title": "The Rare Arena Network",
        "global_context": global_context,
        "sections": sections_data
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)
        
    print(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

