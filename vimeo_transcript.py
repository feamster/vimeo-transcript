#!/usr/bin/env python3
"""
Extract transcripts from Vimeo videos.

This script uses Playwright to navigate to a Vimeo video page, extract the
VTT caption URL from the embedded player, and convert it to plain text.

Usage:
    python vimeo_transcript.py <vimeo_url> [--output FILE] [--format FORMAT]

Examples:
    python vimeo_transcript.py https://vimeo.com/123456789
    python vimeo_transcript.py "https://vimeo.com/showcase/MyShowcase?video=123456789"
    python vimeo_transcript.py https://vimeo.com/123456789 --output transcript.txt
    python vimeo_transcript.py https://vimeo.com/123456789 --format vtt
"""

import argparse
import asyncio
import re
import ssl
import sys
import urllib.request
from urllib.error import URLError


async def extract_vtt_url(url: str) -> str | None:
    """
    Navigate to a Vimeo page and extract the VTT caption URL.

    Args:
        url: The Vimeo video URL

    Returns:
        The VTT caption URL if found, None otherwise
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Error: playwright is required. Install with: pip install playwright", file=sys.stderr)
        print("Then run: playwright install chromium", file=sys.stderr)
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"Loading: {url}", file=sys.stderr)
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Wait for dynamic content
        await asyncio.sleep(5)

        # Get the main page HTML
        html = await page.content()

        # Check for VTT URLs in main page
        vtt_urls = re.findall(r'https://[^"\'<>\s]*captions[^"\'<>\s]*\.vtt[^"\'<>\s]*', html)

        # If not found, try the iframe
        if not vtt_urls:
            iframe = await page.query_selector('iframe[src*="player.vimeo"]')
            if iframe:
                frame = await iframe.content_frame()
                if frame:
                    await asyncio.sleep(3)
                    iframe_html = await frame.content()
                    vtt_urls = re.findall(
                        r'https://[^"\'<>\s]*captions[^"\'<>\s]*\.vtt[^"\'<>\s]*',
                        iframe_html
                    )

        await browser.close()

        if vtt_urls:
            # Clean up the URL (remove HTML entities)
            vtt_url = vtt_urls[0].replace('&amp;', '&').replace('\\u0026', '&')
            return vtt_url

        return None


def download_vtt(vtt_url: str) -> str:
    """
    Download the VTT file content.

    Args:
        vtt_url: URL to the VTT file

    Returns:
        The VTT file content as a string
    """
    print(f"Downloading transcript...", file=sys.stderr)
    try:
        # Create SSL context that doesn't verify certificates
        # (Vimeo's caption CDN sometimes has certificate issues)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(vtt_url, timeout=30, context=ctx) as response:
            return response.read().decode('utf-8')
    except URLError as e:
        print(f"Error downloading VTT: {e}", file=sys.stderr)
        sys.exit(1)


def vtt_to_text(vtt_content: str) -> str:
    """
    Convert VTT format to plain text.

    Args:
        vtt_content: The raw VTT file content

    Returns:
        Plain text transcript with timing information removed
    """
    # Remove WEBVTT header
    content = re.sub(r'^WEBVTT.*?\n\n', '', vtt_content, flags=re.DOTALL)

    lines = content.split('\n')
    text_lines = []

    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip cue numbers (just digits)
        if re.match(r'^\d+$', line):
            continue
        # Skip timestamp lines
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', line):
            continue
        text_lines.append(line)

    # Join and clean up multiple spaces
    transcript = ' '.join(text_lines)
    transcript = re.sub(r'\s+', ' ', transcript)

    return transcript.strip()


def main():
    parser = argparse.ArgumentParser(
        description='Extract transcripts from Vimeo videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('url', help='Vimeo video URL')
    parser.add_argument(
        '-o', '--output',
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'vtt'],
        default='text',
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    # Extract VTT URL from the page
    vtt_url = asyncio.run(extract_vtt_url(args.url))

    if not vtt_url:
        print("Error: Could not find transcript/captions for this video.", file=sys.stderr)
        print("The video may not have captions enabled.", file=sys.stderr)
        sys.exit(1)

    # Download the VTT content
    vtt_content = download_vtt(vtt_url)

    # Convert format if needed
    if args.format == 'text':
        output = vtt_to_text(vtt_content)
    else:
        output = vtt_content

    # Write output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Transcript saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
