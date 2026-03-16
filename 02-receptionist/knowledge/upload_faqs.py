"""
Upload clinic FAQs to Pinecone.
Run once: python knowledge/upload_faqs.py
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from pinecone import Pinecone
except ImportError:
    print("ERROR: pinecone not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    print("ERROR: PINECONE_API_KEY not set in .env")
    sys.exit(1)

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "ai-agent-platform")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "biz_intern_receptionist")

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

faqs_path = Path(__file__).parent / "faqs.json"
with open(faqs_path) as f:
    faqs = json.load(f)

print(f"Uploading {len(faqs)} FAQs to namespace '{NAMESPACE}'...")

records = []
for faq in faqs:
    records.append({
        "_id": faq["id"],
        "question": faq["question"],
        "answer": faq["answer"],
        "category": faq["category"],
        "text": f"{faq['question']} {faq['answer']}"  # combined for embedding
    })

# Upsert in batches of 10
batch_size = 10
for i in range(0, len(records), batch_size):
    batch = records[i:i + batch_size]
    index.upsert_records(NAMESPACE, batch)
    print(f"  Uploaded {min(i + batch_size, len(records))}/{len(faqs)}")

print(f"\nDone! {len(faqs)} FAQs uploaded to namespace '{NAMESPACE}'")
print("Your receptionist bot can now answer FAQ questions using Pinecone.")
