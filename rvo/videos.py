# Work in progress: small temp hacky file.
import logging
from pathlib import Path

import tomlkit

from rvo import utils

logger = logging.getLogger(__name__)

METADATA_DIR = Path("~/zelf/websitecontent/videos").expanduser()
OUTPUT_DIR = Path("~/zelf/reinout.vanrees.org/docs/build/html/videos").expanduser()
TEMPLATE = """\
<!DOCTYPE html>
<html>
  <head>
    <title>{title}</title>
    <meta charset="utf-8" />
  </head>
  <body>
    <h1>{title}</h1>
    <a href="{youtube}">View video on youtube</a>
  </body>
</html>
"""


def main():
    logging.basicConfig(level=logging.INFO)
    for year_dir in METADATA_DIR.glob("????"):
        year = year_dir.name
        output_dir = OUTPUT_DIR / year
        if not output_dir.exists():
            output_dir.mkdir()
        for metadata_file in year_dir.glob("*.toml"):
            metadata = tomlkit.loads(metadata_file.read_text())
            output_filename = metadata_file.stem + ".html"
            output = TEMPLATE.format(
                title=metadata.get("title"),
                youtube=metadata.get("youtube"),
            )
            output_file = output_dir / output_filename
            written = utils.write_if_changed(output_file, output)
            if written:
                # Log remote url.
                print(f"https://reinout.vanrees.org/videos/{year}/{output_filename}")


if __name__ == "__main__":
    main()
