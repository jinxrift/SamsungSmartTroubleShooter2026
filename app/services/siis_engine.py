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

    if "review" in name:
        return "It will help you review the relevant settings"

    if "clear" in name:
        return "It will help you clear temporary app data"

    if "restart" in name:
        return "It will help you restart the device safely"

    if "contact" in name:
        return "It will help you get further assistance"

    if "customize" in name:
        return "It will help you customize device settings"

    if "use" in name:
        return "It will help you use the device feature"

    if "swipe" in name:
        return "It will help you configure swipe gestures"

    if "exit" in name:
        return "It will help you exit the current feature"

    if "create" in name:
        return "It will help you create the desired setup"

    if "remove" in name:
        return "It will help you remove unwanted shortcuts"

    if "touchscreen" in name:
        return "It will help you access your device data"

    if "nothing is visible" in name:
        return "It will help you access data without screen visibility"

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