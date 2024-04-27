# GNU C Manual Beautifier

This python script re parses the HTML generated from the
[GNU C Language Introduction and Reference Manual](https://www.gnu.org/software/c-intro-and-ref/) and adds:

- [x] CSS style sheets 
- [x] Syntax highlighting for code blocks
- [ ] A side panel for navigating between sections
- [x] Improved navbar

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
