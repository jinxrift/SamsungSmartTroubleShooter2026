import re


def extract_sections(content):
    sections = []

    # =========================================================
    # FORMAT 1:
    # Step 1: Heading
    # Step 2: Heading
    # =========================================================
    numbered_pattern = (
        r"(?:#{1,3}\s*)?"
        r"(?:Step\s+)?"
        r"(\d+)[.:]\s*"
        r"(.+?)"
        r"(?=\n(?:#{1,3}\s*)?(?:Step\s+)?\d+[.:]|\Z)"
    )

    numbered_matches = re.findall(
        numbered_pattern,
        content,
        re.IGNORECASE | re.DOTALL
    )

    for number, text in numbered_matches:
        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        if not lines:
            continue

        sections.append({
            "number": int(number),
            "text": "\n".join(lines)
        })

    # =========================================================
    # FORMAT 2:
    # ## Heading
    # content...
    #
    # ## Another Heading
    # content...
    # =========================================================
    heading_pattern = (
        r"^#{1,3}\s+(.+?)\s*$"
        r"(.*?)(?=^#{1,3}\s+.+?$|\Z)"
    )

    heading_matches = re.findall(
        heading_pattern,
        content,
        re.MULTILINE | re.DOTALL
    )

    # Only use heading format if numbered sections
    # were not found.
    if not numbered_matches:

        for index, (heading, text) in enumerate(
            heading_matches,
            start=1
        ):
            heading = heading.strip()

            lines = [
                line.strip()
                for line in text.split("\n")
                if line.strip()
            ]

            if not heading:
                continue

            sections.append({
                "number": index,
                "text": "\n".join(
                    [heading] + lines
                )
            })

    return sections


def generate_description(action_name):
    name = action_name.lower()

    if "check" in name:
        return "It will help you check the device issue"

    if "verify" in name:
        return "It will help you verify the device connection"

    if "restart" in name:
        return "It will help you restart the device safely"

    if "clear" in name:
        return "It will help you clear temporary app data"

    if "contact" in name or "assistance" in name:
        return "It will help you get further assistance"

    if "repair" in name or "service center" in name:
        return "It will help you arrange device repair"

    if "update" in name:
        return "It will help you update the device software"

    if "safe mode" in name:
        return "It will help you check for app-related issues"

    if "factory data reset" in name:
        return "It will help you reset the device"

    if "charger" in name:
        return "It will help you check charging-related issues"

    if "gesture" in name:
        return "It will help you adjust navigation settings"

    if "sensitivity" in name:
        return "It will help you adjust touch sensitivity"

    if "touchscreen doesn't work" in name:
        return "It will help you access your device data"
    
    return "It will help you troubleshoot the reported issue"

def process_siis(query, siis_response):
    title = siis_response.title
    content = siis_response.content

    sections = extract_sections(content)

    goals = [
        {
            "goal": f"Follow these steps to perform this {title} Troubleshooting",
            "title": title,
            "actions": [],
            "score": 0.95
        }
    ]

    for section in sections:

        lines = [
            line.strip()
            for line in section["text"].split("\n")
            if line.strip()
        ]

        if not lines:
            continue

        # First line = action heading
        action_name = lines[0]

        # Remaining lines = actual steps
        steps = lines[1:]

        action = {
            "actionName": action_name,
            "description": generate_description(action_name),
            "stepGroups": [
                {
                    "steps": steps
                }
            ],
            "category": "manual"
        }

        goals[0]["actions"].append(action)

    return {
        "goals": goals
    }