# Storybox

RFID-triggered audio player for Raspberry Pi Zero W. Place an RFID card on the reader to play its mapped audio clip; remove the card to stop playback.

## Hardware

- Raspberry Pi Zero W (v1.1)
- MFRC522 RFID reader (SPI)
- WM8960 Audio HAT (I2S/I2C)
- Speaker connected to WM8960

## Wiring

### MFRC522 to Pi Zero W

| MFRC522 Pin | Pi GPIO | Pi Physical Pin |
|-------------|---------|-----------------|
| SDA         | GPIO 8 (CE0) | 24 |
| SCK         | GPIO 11 | 23 |
| MOSI        | GPIO 10 | 19 |
| MISO        | GPIO 9  | 21 |
| RST         | GPIO 25 | 22 |
| GND         | GND     | 6  |
| 3.3V        | 3V3     | 1  |
| IRQ         | (not connected) | - |

The WM8960 Audio HAT connects via the full 40-pin header (I2C on GPIO 2/3, I2S on GPIO 18-21).

## Setup

1. Flash Raspberry Pi OS Lite (Bookworm, 32-bit) to your SD card
2. Install the WM8960 driver:

```bash
git clone https://github.com/waveshare/WM8960-Audio-HAT
cd WM8960-Audio-HAT
sudo ./install.sh
sudo reboot
```

3. Clone this repo and run the installer:

```bash
cd /home/pi
git clone <your-repo-url> storybox
cd storybox
sudo ./install.sh
```

4. Verify audio output:

```bash
aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Center.wav
```

## Usage

### Registering Cards

SSH into the Pi and run the registration script:

```bash
cd /home/pi/storybox
sudo venv/bin/python src/register.py
```

Follow the prompts to place a card and select an audio file from the `audio/` directory.

### Adding Audio Files

Copy WAV files into the `audio/` directory:

```bash
scp story.wav pi@storybox.local:/home/pi/storybox/audio/
```

Files must be in WAV format. Convert other formats with ffmpeg:

```bash
ffmpeg -i story.mp3 -ar 44100 -ac 2 audio/story.wav
```

### Service Management

The storybox service starts automatically on boot. Manual control:

```bash
sudo systemctl status storybox
sudo systemctl restart storybox
sudo systemctl stop storybox
sudo journalctl -u storybox -f
```

## How It Works

The main daemon polls the MFRC522 reader every 200ms. When a card is detected, it looks up the card's UID in `mappings.json`. If a mapping exists, it starts playing the associated audio file via `aplay` through the WM8960 codec. When the card is removed (3 consecutive failed reads for debouncing), playback stops.

## Project Structure

```
storybox/
  src/
    storybox.py      # Main daemon
    register.py      # Card registration utility
  audio/             # WAV files
  mappings.json      # Card UID to audio file mappings
  storybox.service   # systemd unit
  install.sh         # Setup script
  requirements.txt   # Python dependencies
```
