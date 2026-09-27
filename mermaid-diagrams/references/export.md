# Export a file

Use this only when the user asks for an SVG, PNG, or PDF. The GitHub fence from `SKILL.md` still comes first. A local `mmdc` is often a newer Mermaid than GitHub, so the file can lay out differently from the fence on github.com.

1. Write the same source to a `.mmd` file.
2. Render with `mmdc`. Read `mmdc --help` for flags. Do not install a package.
3. When Chromium reports a sandbox error, write `{"args":["--no-sandbox"]}` to a puppeteer config file and pass it with `-p`.
4. Done when `mmdc` exits 0 and the reply includes the output path.

When `mmdc` is not on `PATH`, return the fence and name the missing command.
