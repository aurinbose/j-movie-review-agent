from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DEFAULT_PROMPT_FILE = Path("outputs/prompts/prompts.xlsx")


def build_video_prompt(title: str, review_text: str) -> str:
    return (
        "Create a fast paced video for YouTube Shorts about "
        f"{title} Movie Review. Review text for reference is as below:\n\n"
        f"{review_text}\n\n"
        "Settings:\n"
        "Make the background music Trendy and Catchy\n"
        "Add any subtitle"
    )


def append_prompt_to_excel(prompt: str, prompt_file: Path = DEFAULT_PROMPT_FILE) -> Path:
    prompt_file = Path(prompt_file)
    prompt_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

    if prompt_file.exists():
        try:
            df = pd.read_excel(prompt_file)
        except Exception:
            df = pd.DataFrame(columns=["created_at", "prompt"])
    else:
        df = pd.DataFrame(columns=["created_at", "prompt"])

    new_row = pd.DataFrame([
        {"created_at": timestamp, "prompt": prompt}
    ])

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(prompt_file, index=False)
    return prompt_file
