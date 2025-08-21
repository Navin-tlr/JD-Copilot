#!/usr/bin/env python3
"""
Process Real PDFs with LLM Extraction
Uses the working LLM extraction to process your actual PDF files
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ingest.structured_extractor import StructuredExtractor

def process_real_pdfs():
    """Process real PDFs using LLM extraction"""
    print("🚀 Processing Real PDFs with LLM Extraction")
    print("=" * 50)
    
    # Initialize the extractor
    extractor = StructuredExtractor()
    
    # Get PDF files from your data directory
    pdf_dir = Path("data/jds")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/jds/")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    successful_extractions = []
    
    for pdf_file in pdf_files:
        print(f"\n📄 Processing: {pdf_file.name}")
        print("-" * 40)
        
        try:
            # Read the PDF text (you'll need to implement PDF reading)
            # For now, let's use the HTML content if available
            html_file = Path(f"data/langext_html/{pdf_file.stem}.html")
            
            if html_file.exists():
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract text from HTML (simple approach)
                import re
                text_content = re.sub(r'<[^>]+>', ' ', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                
                print(f"   📝 Text length: {len(text_content)} characters")
                
                # Extract structured data using LLM
                extraction = extractor.extract_structured_data(text_content)
                
                if extraction:
                    print(f"✅ LLM Extraction Successful!")
                    print(f"   Company: {extraction.company_name}")
                    print(f"   Roles: {len(extraction.roles)}")
                    
                    for role in extraction.roles:
                        print(f"   - {role.title}")
                        if role.skills:
                            print(f"     Skills: {', '.join(role.skills[:3])}...")
                    
                    # Save to file
                    output_file = extractor.save_structured_data(extraction, pdf_file.name)
                    print(f"   💾 Saved to: {output_file}")
                    
                    successful_extractions.append({
                        "pdf_file": pdf_file.name,
                        "extraction": extraction,
                        "output_file": output_file
                    })
                    
                else:
                    print("❌ LLM Extraction Failed")
                    
            else:
                print(f"⚠️ No HTML content found for {pdf_file.name}")
                
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n🎯 Processing Complete!")
    print(f"✅ Successfully processed: {len(successful_extractions)}/{len(pdf_files)} PDFs")
    
    if successful_extractions:
        print(f"\n📊 Extracted Companies:")
        for item in successful_extractions:
            print(f"   - {item['extraction'].company_name}: {len(item['extraction'].roles)} roles")
    
    print(f"\nNext steps:")
    print("1. Review the extracted JSON files")
    print("2. Populate the database with LLM-extracted data")
    print("3. Compare with manual extraction quality")

if __name__ == "__main__":
    process_real_pdfs()
