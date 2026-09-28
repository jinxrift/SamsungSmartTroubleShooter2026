import json
from openai import OpenAI

client = OpenAI()


SYSTEM_PROMPT = """
You are a troubleshooting information extraction engine.

Your job is to extract actionable troubleshooting information
from the provided SIIS response.

Rules:
1. Do not invent troubleshooting steps.
2. Use only information present in the SIIS response.
3. Identify actual troubleshooting actions.
4. Ignore purely explanatory sections unless they contain an actionable instruction.
5. Preserve the original meaning of the troubleshooting steps.
6. Return valid JSON only.

Output format:

{
  "actions": [
    {
      "actionName": "string",
      "description": "string",
      "steps": [
        "string"
      ],
      "category": "manual"
    }
  ]
}

The category must be one of:
- auto
- manual
- critical
"""


def extract_with_llm(query, title, content):
    prompt = f"""
User query:
{query}

SIIS title:
{title}

SIIS response:
{content}

Extract the troubleshooting actions and steps.
"""

    response = client.chat.completions.create(
        model="gpt-5.6",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    text = response.choices[0].message.content

    return json.loads(text)