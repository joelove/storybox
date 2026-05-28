import json
import sys
import time
from pathlib import Path

from mfrc522 import MFRC522

BASE_DIR = Path(__file__).resolve().parent.parent
MAPPINGS_FILE = BASE_DIR / "mappings.json"
AUDIO_DIR = BASE_DIR / "audio"


def load_mappings() -> dict[str, str]:
    if not MAPPINGS_FILE.is_file():
        return {}
    with open(MAPPINGS_FILE, "r") as f:
        return json.load(f)


def save_mappings(mappings: dict[str, str]) -> None:
    with open(MAPPINGS_FILE, "w") as f:
        json.dump(mappings, f, indent=2)


def uid_to_string(uid: list[int]) -> str:
    return ":".join(f"{byte:02X}" for byte in uid)


def list_audio_files() -> list[str]:
    if not AUDIO_DIR.is_dir():
        return []
    extensions = {".wav", ".WAV"}
    return sorted(
        f.name for f in AUDIO_DIR.iterdir() if f.suffix in extensions and f.is_file()
    )


def read_card_blocking(reader: MFRC522) -> str:
    print("Place a card on the reader...")
    while True:
        (status, _) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                return uid_to_string(uid)
        time.sleep(0.2)


def select_audio_file(files: list[str]) -> str | None:
    if not files:
        print("\nNo audio files found in audio/ directory.")
        print("Add WAV files to the audio/ directory and try again.")
        return None

    print("\nAvailable audio files:")
    for i, name in enumerate(files, 1):
        print(f"  {i}. {name}")

    while True:
        choice = input(f"\nSelect a file (1-{len(files)}): ").strip()
        if not choice:
            return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(files):
                return files[index]
        except ValueError:
            pass
        print("Invalid selection, try again.")


def main() -> None:
    print("=" * 40)
    print("  Storybox - Card Registration")
    print("=" * 40)

    reader = MFRC522()
    mappings = load_mappings()

    print(f"\nCurrently registered: {len(mappings)} card(s)")
    if mappings:
        print("\nExisting mappings:")
        for uid, audio in mappings.items():
            print(f"  {uid} -> {audio}")

    while True:
        print("\n" + "-" * 40)
        audio_files = list_audio_files()

        audio_file = select_audio_file(audio_files)
        if audio_file is None:
            break

        uid = read_card_blocking(reader)
        print(f"\nCard detected: {uid}")

        if uid in mappings:
            existing = mappings[uid]
            confirm = input(
                f"This card is already mapped to '{existing}'. Overwrite? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("Skipped.")
                continue

        mappings[uid] = audio_file
        save_mappings(mappings)
        print(f"Registered: {uid} -> {audio_file}")

        again = input("\nRegister another card? (y/n): ").strip().lower()
        if again != "y":
            break

    print("\nDone.")


if __name__ == "__main__":
    main()
