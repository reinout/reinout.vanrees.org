# Work in progress: small temp hacky file.
from pathlib import Path
import tomlkit


METADATA_DIR = Path("~/zelf/websitecontent/videos").expanduser()
OUTPUT_DIR = Path("~/zelf/reinout.vanrees.org/docs/build/html/videos").expanduser()
TEMPLATE = """
<html>
  <head><title>{title}</title></head>
  <body>
    <h1>{title}</h1>
    <a href="{youtube}">View video on youtube</a>
  </body>
</html>
"""


for year_dir in METADATA_DIR.glob("????"):
    year = year_dir.name
    output_dir = OUTPUT_DIR / year
    if not output_dir.exists():
        output_dir.mkdir()
    for metadata_file in year_dir.glob("*.toml"):
        metadata = tomlkit.load(metadata_file.open())
        output_filename = metadata_file.stem + ".html"
        output = TEMPLATE.format(
            title=metadata.get("title"),
            youtube=metadata.get("youtube"),
        )
        output_file = output_dir / output_filename
        output_file.write_text(output)
        print(f"Wrote {output_file}")
