from pdf_parser import extract_text

text = extract_text("papers/2201.00978v1.pdf")
print(text[:500])
print(f"\nTotal characters: {len(text)}")