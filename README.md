# GNU C Manual Beautifier

This python script re parses the GNU C Manual HTML and adds:

- [x] CSS style sheets 
- [ ] Syntax highlighting for code blocks
- [ ] A side panel navigating between sections

# Generate Manual

Clone the repo and download dependencies:

```bash
git clone --recursive https://github.com/ValdezFOmar/gnu-c-manual-beautifier
cd gnu-c-manual-beautifier
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Then `cd` into the `gnu-c-manual` git sub module and generate the HTML.

```bash
cd gnu-c-manual
make c.html.d
```

Lastly, got back to the root of the repo and beautify the html:

```bash
python beautify.py --html --css
```
