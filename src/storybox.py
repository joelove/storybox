import json
import logging
import signal
import subprocess
import sys
import time
from pathlib import Path

from mfrc522 import MFRC522

BASE_DIR = Path(__file__).resolve().parent.parent
MAPPINGS_FILE = BASE_DIR / "mappings.json"
AUDIO_DIR = BASE_DIR / "audio"
ALSA_DEVICE = "hw:1,0"
POLL_INTERVAL = 0.2
REMOVAL_THRESHOLD = 3

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("storybox")


class AudioPlayer:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._current_file: str | None = None

    @property
    def is_playing(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def current_file(self) -> str | None:
        if self.is_playing:
            return self._current_file
        return None

    def play(self, audio_path: str) -> None:
        if self.current_file == audio_path:
            return
        self.stop()
        resolved = AUDIO_DIR / audio_path
        if not resolved.is_file():
            logger.warning("Audio file not found: %s", resolved)
            return
        logger.info("Playing: %s", audio_path)
        self._process = subprocess.Popen(
            ["aplay", "-D", ALSA_DEVICE, "--quiet", str(resolved)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._current_file = audio_path

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            logger.info("Stopping playback")
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None
        self._current_file = None


def load_mappings() -> dict[str, str]:
    if not MAPPINGS_FILE.is_file():
        return {}
    with open(MAPPINGS_FILE, "r") as f:
        return json.load(f)


def uid_to_string(uid: list[int]) -> str:
    return ":".join(f"{byte:02X}" for byte in uid)


def read_card(reader: MFRC522) -> str | None:
    (status, tag_type) = reader.MFRC522_Request(reader.PICC_REQIDL)
    if status != reader.MI_OK:
        return None
    logger.debug("Card present (tag_type=%s)", tag_type)
    (status, uid) = reader.MFRC522_Anticoll()
    if status != reader.MI_OK:
        logger.debug("Anticollision failed")
        return None
    uid_str = uid_to_string(uid)
    logger.debug("Read UID: %s", uid_str)
    return uid_str


def main() -> None:
    logger.info("Storybox starting")

    reader = MFRC522()
    player = AudioPlayer()
    mappings = load_mappings()
    logger.info("Loaded %d card mapping(s)", len(mappings))

    absent_count = 0
    running = True

    def handle_shutdown(signum, frame):
        nonlocal running
        logger.info("Shutdown signal received")
        running = False

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        while running:
            uid = read_card(reader)

            if uid is not None:
                absent_count = 0
                audio_file = mappings.get(uid)
                if audio_file:
                    if player.current_file != audio_file:
                        logger.debug("Mapped UID %s -> %s", uid, audio_file)
                        player.play(audio_file)
                    elif not player.is_playing:
                        logger.debug("Restarting finished playback for %s", audio_file)
                        player.play(audio_file)
                else:
                    logger.debug("Unknown card: %s", uid)
            else:
                absent_count += 1
                if absent_count >= REMOVAL_THRESHOLD and player.is_playing:
                    player.stop()

            time.sleep(POLL_INTERVAL)
    finally:
        player.stop()
        logger.info("Storybox stopped")


if __name__ == "__main__":
    main()
