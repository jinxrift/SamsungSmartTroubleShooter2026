from app.deeplink.matcher import DeeplinkMatcher

matcher = DeeplinkMatcher("data/deeplinks.json")

action_name = "Change Touch and Hold Delay"
description = "Adjust the touch and hold delay."
steps = [
    "Open Settings.",
    "Tap Accessibility.",
    "Tap Touch and hold delay.",
    "Adjust the delay.",
]

result = matcher.build_step_group_result(action_name, description, steps)


print("\nACTIONABLE DEEPLINK:")
print(result["actionableDeeplink"])

print("\nVALIDATION DEEPLINK:")
print(result["validationDeeplink"])
