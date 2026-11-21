"""Build the submission presentation PDF from slajdy.html with headless Chrome or Chromium.

    python3 -B submission/prezentacja/build-pdf.py [--chrome <path>]

Writes submission/mapa-serc-prezentacja.pdf and prints its size and page count. Exit 1 when the PDF is missing,
larger than 10 MB (HackTribe limit) or has fewer than 5 pages (challenge requirement). Also renders okladka.html
to submission/mapa-serc-okladka-hacktribe.png (800 x 600, the HackTribe project cover)."""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'slajdy.html'
OUTPUT = HERE.parent / 'mapa-serc-prezentacja.pdf'
LIMIT = 10 * 1024 * 1024
COVER_SOURCE = HERE / 'okladka.html'
COVER = HERE.parent / 'mapa-serc-okladka-hacktribe.png'
CANDIDATES = (
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome',
)


def find_chrome(explicit):
    for name in ([explicit] if explicit else CANDIDATES):
        path = shutil.which(name) or (name if Path(name).is_file() else None)
        if path:
            return path
    sys.exit('Chrome or Chromium not found; pass --chrome <path>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chrome')
    args = parser.parse_args()
    chrome = find_chrome(args.chrome)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-first-run', '--user-data-dir=' + profile,
                        '--no-pdf-header-footer', '--print-to-pdf=' + str(OUTPUT), SOURCE.as_uri()],
                       check=True, capture_output=True, timeout=180)
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-first-run', '--user-data-dir=' + profile,
                        '--hide-scrollbars', '--force-device-scale-factor=1', '--window-size=800,600',
                        '--screenshot=' + str(COVER), COVER_SOURCE.as_uri()],
                       check=True, capture_output=True, timeout=180)
    print('{} {:.0f} kB'.format(COVER.name, COVER.stat().st_size / 1024))
    data = OUTPUT.read_bytes()
    pages = len(re.findall(rb'/Type\s*/Page[^s]', data))
    print('{} {:.2f} MB, {} pages'.format(OUTPUT.name, len(data) / 1024 / 1024, pages))
    if len(data) > LIMIT or pages < 5:
        sys.exit('PDF must be at most 10 MB and have at least 5 pages')


if __name__ == '__main__':
    main()
