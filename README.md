# Audio File Cutter

A Python application that cuts arbitrary length segments from audio files - from the front, back, or middle.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The application supports multiple cutting operations:

### Cut from Front
Remove a specified duration from the beginning:
```bash
python audio_cutter.py input.mp3 --cut-front 10s -o output.mp3
```

### Cut from Back  
Remove a specified duration from the end:
```bash
python audio_cutter.py input.mp3 --cut-back 5s -o output.mp3
```

### Cut from Middle
Remove a section between two time points:
```bash
python audio_cutter.py input.mp3 --cut-middle 1:00 2:30 -o output.mp3
```

### Extract Segment
Extract only a specific section (opposite of cut-middle):
```bash
python audio_cutter.py input.mp3 --extract 1:00 2:30 -o output.mp3
```

## Time Format

Supports multiple time formats:
- `5s` - 5 seconds
- `500ms` - 500 milliseconds  
- `1:30` - 1 minute 30 seconds
- `1:23:45` - 1 hour 23 minutes 45 seconds
- `75.5` - 75.5 seconds

## Options

- `--format` - Specify output format (mp3, wav, etc.). Auto-detected from extension if not specified
- `--info` - Show audio file information
- `-o, --output` - Output file path (required)

## Supported Formats

The application supports all audio formats supported by pydub, including:
- MP3
- WAV
- FLAC
- AAC
- OGG
- And many more

## Examples

```bash
# Remove first 30 seconds
python audio_cutter.py song.mp3 --cut-front 30s -o song_trimmed.mp3

# Remove last 10 seconds  
python audio_cutter.py podcast.wav --cut-back 10s -o podcast_clean.wav

# Remove a middle section (e.g., remove ads from 2:15 to 2:45)
python audio_cutter.py podcast.mp3 --cut-middle 2:15 2:45 -o podcast_no_ads.mp3

# Extract just the chorus (from 1:20 to 1:50)
python audio_cutter.py song.mp3 --extract 1:20 1:50 -o chorus.mp3

# Show file info
python audio_cutter.py song.mp3 --info --cut-front 0s -o temp.mp3
```