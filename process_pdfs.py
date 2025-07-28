import os
import json
from pathlib import Path
import pymupdf
from math import ceil
import re


def clean_bytes(data_obj):
    """Recursively clean binary data from dict/list."""
    if isinstance(data_obj, dict):
        return {key: clean_bytes(value) for key, value in data_obj.items()}
    elif isinstance(data_obj, list):
        return [clean_bytes(item) for item in data_obj]
    elif isinstance(data_obj, bytes):
        return "<binary data>"
    return data_obj


def smart_merge(existing_text, new_text):
    """Merge overlapping text fragments."""
    existing_text = existing_text.strip()
    new_text = new_text.strip()

    if new_text in existing_text:
        return existing_text
    if existing_text in new_text:
        return new_text

    max_overlap = 0
    min_len = min(len(existing_text), len(new_text))
    for i in range(1, min_len):
        if existing_text[-i:] == new_text[:i]:
            max_overlap = i

    return existing_text + new_text[max_overlap:]


def clean_heading_text(text: str) -> str:
    """Remove bullets, symbols, and extra spaces."""
    text = text.strip()

    text = re.sub(r"[\u2022\u25cf•▪►\*]", " ", text)   
    text = re.sub(r"[-_=]{2,}", " ", text)              
    text = re.sub(r"\s+", " ", text)                   
    return text.strip()


def is_valid_heading(text: str) -> bool:
    """Check if heading text is meaningful."""
    text = text.strip()

    if not text:
        return False
    if re.fullmatch(r"[^A-Za-z0-9]+", text):            
        return False
    if len(text) < 3:                                   
        return False
    if re.search(r"(www\.|http|@)", text.lower()):      
        return False
    return True


def process_pdfs():
    
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")

    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[ERROR] No PDF files found in {input_dir.resolve()}")
        return

    for pdf_file in pdf_files:
        print(f"[INFO] Processing {pdf_file.name}...")

        doc = pymupdf.open(pdf_file)
        all_pages_data = []

        for page_num, page in enumerate(doc, start=1):
            page_data = page.get_text("dict")
            cleaned_page_data = clean_bytes(page_data)

            all_pages_data.append({
                "page_number": page_num,
                "content": cleaned_page_data
            })

        text_dict = {}
        for page in all_pages_data:
            page_num = page["page_number"]

            for block in page["content"]["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        key = (page_num, span["size"], span["ascender"],
                               span["descender"], span.get("font", ""))
                        text = span["text"].strip()

                        if key in text_dict:
                            text_dict[key] = smart_merge(text_dict[key], text)
                        else:
                            text_dict[key] = text

        sorted_items = sorted(text_dict.items(), key=lambda item: item[0][1], reverse=True)

        unique_sizes, seen = [], set()
        for (_, size, _, _, _), _ in sorted_items:
            if size not in seen:
                unique_sizes.append(size)
                seen.add(size)
            if len(unique_sizes) == 4:
                break

        title_size = unique_sizes[0] if unique_sizes else 20
        h1_base = ceil(unique_sizes[1] / 5.0) * 5 if len(unique_sizes) > 1 else title_size

        heading_ranges = {
            "H1": (h1_base - 4, h1_base),
            "H2": (h1_base - 9, h1_base - 5),
            "H3": (h1_base - 14, h1_base - 10)
        }

        output = {"title": "", "outline": []}

        for (page, size, asc, desc, font), text in sorted_items:
            text = clean_heading_text(text)
            if not is_valid_heading(text):
                continue

            if size == title_size and not output["title"]:
                output["title"] = text
                continue

            if size < 11:
                continue

            for level, (low, high) in heading_ranges.items():
                if low <= size <= high:
                    output["outline"].append({
                        "level": level,
                        "text": text,
                        "page": page
                    })
                    break

        output_file = output_dir / f"{pdf_file.stem}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] {pdf_file.name} -> {output_file.name}")


if __name__ == "__main__":
    print("[START] PDF Processing")
    process_pdfs()
    print("[DONE] All PDFs processed")
