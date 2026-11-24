#!/usr/bin/env python3
"""Render PlantUML diagrams to PNG and size them for the doc builder.

    diagram.py diagrams/foo.puml [diagrams/bar.puml ...]

Uses `plantuml` on PATH, else `java -jar $PLANTUML_JAR`. Each .puml should start with
`!include <skill dir>/assets/style.iuml` (absolute path). After rendering, each PNG's DPI is set
so it lands at most 6.3 in wide and 4.6 in tall (pandoc sizes images by DPI).
"""
import os, shutil, subprocess, sys

MAX_W, MAX_H = 6.3, 4.6


def plantuml():
    if shutil.which("plantuml"):
        return ["plantuml"]
    jar = os.environ.get("PLANTUML_JAR")
    if jar and os.path.exists(jar):
        return ["java", "-jar", jar]
    sys.exit("PlantUML not found: install `plantuml` or set PLANTUML_JAR=/path/to/plantuml.jar")


def main(paths):
    if not paths:
        sys.exit(__doc__)
    from PIL import Image
    subprocess.run(plantuml() + ["-tpng"] + paths, check=True)
    for p in paths:
        png = os.path.splitext(p)[0] + ".png"
        img = Image.open(png)
        w, h = img.size
        dpi = max(w / MAX_W, h / MAX_H, 72)
        img.save(png, dpi=(dpi, dpi))
        print(f"{png}: {w}x{h}px @ {dpi:.0f} dpi -> {w/dpi:.2f}x{h/dpi:.2f} in")


if __name__ == "__main__":
    main(sys.argv[1:])
