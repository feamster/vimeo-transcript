# vimeo-transcript

Extract transcripts from Vimeo videos that have captions enabled.

## Installation

```bash
pip install playwright
playwright install chromium
```

## Usage

```bash
# Output transcript to stdout
python vimeo_transcript.py https://vimeo.com/123456789

# Save to a file
python vimeo_transcript.py https://vimeo.com/123456789 --output transcript.txt

# Output in VTT format (with timestamps)
python vimeo_transcript.py https://vimeo.com/123456789 --format vtt

# Works with showcase URLs too
python vimeo_transcript.py "https://vimeo.com/showcase/MyShowcase?video=123456789"
```

## Options

- `-o, --output FILE` - Save transcript to a file instead of stdout
- `-f, --format {text,vtt}` - Output format (default: text)

## Requirements

- Python 3.10+
- playwright

## How it works

The script uses Playwright to:
1. Navigate to the Vimeo video page
2. Extract the VTT caption URL from the embedded player
3. Download the VTT file
4. Convert it to plain text (or output raw VTT if requested)

## Limitations

- Only works for videos that have captions/transcripts enabled
- Requires the video to be publicly accessible (or the showcase to be accessible)
