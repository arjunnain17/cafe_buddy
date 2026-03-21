import os
# test_ingestion.py — run from project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.menu_ingestion import ingest_menu_from_pdf
print(os.path.abspath("Untitled.pdf"))
summary = ingest_menu_from_pdf("Untitled.pdf")
print("\nSummary:", summary)