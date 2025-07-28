import os
import json
from pathlib import Path
import pymupdf  
from math import ceil

def clean_bytes(data_obj):
    if isinstance(data_obj, dict):
        return {key: clean_bytes(value) for key, value in data_obj.items()}
    elif isinstance(data_obj, list):
        return [clean_bytes(item) for item in data_obj]
    elif isinstance(data_obj, bytes):
        return "<binary data>"
    else:
        return data_obj
    

def smart_merge(existing_text, new_text):
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

    merged = existing_text + new_text[max_overlap:]
    return merged
    
def process_pdfs():

    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    for pdf_file in pdf_files:
        doc = pymupdf.open(pdf_file)
        all_pages_data = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"Processing page {page_num + 1}/{len(doc)}...")

            page_data = page.get_text("dict")

            cleaned_page_data = clean_bytes(page_data)
            
            all_pages_data.append({
                "page_number": page_num + 1,
                "content": cleaned_page_data
            })
        
        data = {
            "document_metadata": {
                "source_pdf": os.path.basename(pdf_file),
                "total_pages": len(doc)
            },
            "pages": all_pages_data
        }

        text_dict = {}
        for page in data["pages"]:
            page_num = page["page_number"]

            for block in page["content"]["blocks"]:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        key = (
                            page_num,
                            span["size"],
                            span["ascender"],
                            span["descender"],
                            span.get("font", "")
                        )
                        text = span["text"].strip()

                        if key in text_dict:
                            text_dict[key] = smart_merge(text_dict[key], text)
                        else:
                            text_dict[key] = text

        sorted_items = sorted(text_dict.items(), key=lambda item: item[0][1], reverse=True)
        unique_sizes = []
        seen = set()
        for (page, size, asc, desc, font), text in sorted_items:
            if size not in seen:
                unique_sizes.append(size)
                seen.add(size)
            if len(unique_sizes) == 4:  
                break

        title_size = unique_sizes[0]
        h1_base = ceil(unique_sizes[1] / 5.0) * 5

        heading_ranges = {
            "H1": (h1_base - 4, h1_base),
            "H2": (h1_base - 9, h1_base - 5),
            "H3": (h1_base - 14, h1_base - 10)
        }
        output = {
            "title": "",
            "outline": []
        }
        for (page, size, asc, desc, font), text in sorted_items:
            if size == title_size and output["title"] == "":
                output["title"] = text
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
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"Processed {pdf_file.name} -> {output_file.name}")

if __name__== "__main__":
    print("Starting processing pdfs")
    process_pdfs() 
    print("completed processing pdfs")