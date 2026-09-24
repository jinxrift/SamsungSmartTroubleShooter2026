import json
import re
from collections import Counter

INPUT_FILE = "data/siis_responses.json"
OUTPUT_FILE = "siis_structure_report.txt"


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


responses = data["responses"]

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

    out.write("SIIS STRUCTURE INSPECTION REPORT\n")
    out.write("=" * 100 + "\n\n")

    out.write(f"Total responses: {len(responses)}\n\n")

    # --------------------------------------------------
    # 1. Heading pattern summary
    # --------------------------------------------------

    heading_counter = Counter()

    for response in responses:
        content = response["siis_response"]["content"]

        headings = re.findall(r"(?m)^(#{1,6})\s+(.+)$", content)

        for hashes, heading in headings:
            heading_counter[hashes] += 1

    out.write("HEADING PATTERN SUMMARY\n")
    out.write("-" * 100 + "\n")

    for hashes, count in sorted(
        heading_counter.items(), key=lambda x: (-len(x[0]), x[0])
    ):
        out.write(f"{hashes} headings: {count}\n")

    out.write("\n\n")

    # --------------------------------------------------
    # 2. Detailed response inspection
    # --------------------------------------------------

    for response in responses:

        response_id = response["id"]
        query = response["original_query"]
        title = response["siis_response"]["title"]
        content = response["siis_response"]["content"]

        out.write("=" * 100 + "\n")
        out.write(f"ID: {response_id}\n")
        out.write(f"QUERY: {query}\n")
        out.write(f"TITLE: {title}\n")
        out.write("-" * 100 + "\n")

        # Find headings
        headings = re.findall(r"(?m)^(#{1,6})\s+(.+)$", content)

        out.write("\nHEADINGS FOUND:\n")

        if headings:
            for hashes, heading in headings:
                out.write(f"  {hashes} {heading}\n")
        else:
            out.write("  NONE\n")

        # Detect numbered step patterns
        numbered_patterns = []

        for line in content.splitlines():

            stripped = line.strip()

            if re.match(r"^#{1,6}\s+\d+\.", stripped):
                numbered_patterns.append("heading-number-dot")

            elif re.match(r"^#{1,6}\s+Step\s+\d+[:.]", stripped, re.IGNORECASE):
                numbered_patterns.append("heading-step-number")

            elif re.match(r"^\d+\.\s+", stripped):
                numbered_patterns.append("plain-numbered-list")

            elif re.match(r"^[-*]\s+", stripped):
                numbered_patterns.append("bullet-list")

        out.write("\nSTRUCTURE TYPES DETECTED:\n")

        if numbered_patterns:
            for pattern in sorted(set(numbered_patterns)):
                out.write(f"  - {pattern}\n")
        else:
            out.write("  NONE\n")

        # Show actual numbered/step headings
        out.write("\nSTEP-LIKE HEADINGS:\n")

        step_headings = []

        for hashes, heading in headings:

            if re.search(r"\bStep\s+\d+\b", heading, re.IGNORECASE) or re.match(
                r"^\d+\.", heading
            ):
                step_headings.append(f"{hashes} {heading}")

        if step_headings:
            for heading in step_headings:
                out.write(f"  {heading}\n")
        else:
            out.write("  NONE\n")

        # Show content length
        out.write("\nCONTENT STATISTICS:\n")
        out.write(f"  Characters: {len(content)}\n")
        out.write(f"  Lines: {len(content.splitlines())}\n")
        out.write(f"  Words: {len(content.split())}\n")

        out.write("\n")

    # --------------------------------------------------
    # 3. Final summary
    # --------------------------------------------------

    out.write("=" * 100 + "\n")
    out.write("END OF SIIS STRUCTURE REPORT\n")
    out.write("=" * 100 + "\n")


print(f"Report created: {OUTPUT_FILE}")
