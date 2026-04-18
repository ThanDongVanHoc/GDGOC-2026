"""Quick verification of Phase 3 output."""
import json

with open("dummy_data/phase3_result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

p3 = data["output_phase_3"]
safe = p3["context_safe_localized_text_pack"]
log = p3["localization_log"]
images = p3["Images"]

print("=== LOCALIZATION LOG ===")
for e in log:
    print(f"  {e['original']:20} -> {e['proposed']:20} [{e['status']}]")

print(f"\n=== CHANGED BLOCKS (original != localized) ===")
changed = [b for b in safe if b["original_content"] != b["localized_content"]]
print(f"Total changed: {len(changed)}")
for b in changed[:5]:
    print(f"  Page {b['page_id']}:")
    print(f"    orig: {b['original_content'][:100]}...")
    print(f"    loc:  {b['localized_content'][:100]}...")
    print()

print(f"=== IMAGE REPLACEMENTS (first 3) ===")
for img in images[:3]:
    meta = img[0]
    reps = img[1].get("replacements_json", {})
    print(f"  Image {meta.get('image_index')}: {reps}")
