# Work in progress: small temp hacky file.
import logging
from collections import defaultdict
from pathlib import Path

import tomlkit

from rvo import utils

logger = logging.getLogger(__name__)

METADATA_DIR = Path("~/zelf/websitecontent/videos").expanduser()
OUTPUT_DIR = Path("~/zelf/websitecontent/source/videos").expanduser()
TEMPLATE = """\
# {title}

View video on youtube: {youtube}
"""
INDEX_TEMPLATE = """\
# {title}

```{{toctree}}
{items}
```
"""


def main():
    years = defaultdict(dict)
    logging.basicConfig(level=logging.INFO)
    for year_dir in METADATA_DIR.glob("????"):
        year = year_dir.name
        output_dir = OUTPUT_DIR / year
        if not output_dir.exists():
            output_dir.mkdir()
        for metadata_file in year_dir.glob("*.toml"):
            id = metadata_file.stem
            metadata = tomlkit.loads(metadata_file.read_text())
            output_filename = id + ".md"
            years[year][id] = metadata
            output = TEMPLATE.format(
                title=metadata.get("title"),
                youtube=metadata.get("youtube"),
            )
            output_file = output_dir / output_filename
            written = utils.write_if_changed(output_file, output)
            if written:
                # Log remote url.
                print(f"https://reinout.vanrees.org/videos/{year}/{id}.html")
        video_files = [f"{id}.md" for id in years[year]]
        output = INDEX_TEMPLATE.format(
            title=year,
            items="\n".join(video_files),
        )
        output_file = output_dir / "index.md"
        utils.write_if_changed(output_file, output)

    year_files = [f"{year}/index.md" for year in years]
    output = INDEX_TEMPLATE.format(
        title="Videos",
        items="\n".join(year_files),
    )
    output_file = OUTPUT_DIR / "index.md"
    utils.write_if_changed(output_file, output)


if __name__ == "__main__":
    main()
