#!/opt/homebrew/bin/python3

# Run June 25, 2024.
#
# A very primitive syntactically-oriented script for adding HTMLElementTagName declarations to files
# that don't have one. Note that it has a lot of failure conditions; it can only handle files where
# there is one and only one HTMLElement-derived class, it must be concrete not abstract, and the
# `extends` clause must be on the same line as the `class` token or it won't find it.
#
# Shortcomings aside, there were 360 web components in our system that lacked entries into the
# HTMLElementTagName global space and about 95% of them were fixed with this pass; the rest were
# done by hand.
#
# Usage:
#
# for i in $(rg -l customElement src/); do python add-global $i ; done
# 


import re
import sys

customElement_re = re.compile(r'customElement\("([^"]+)"')
class_re = re.compile(r'class\s+(\w+)\s+extends')
tagmap_re = re.compile(r'interface HTMLElementTagNameMap')

def inject(fn):
    with open(fn, "r", encoding="utf-8") as elemfile:
        content = list(enumerate(elemfile.readlines()))

    searchCustomElement = [l for l in content if customElement_re.search(l[1])]
    searchClass = [l for l in content if class_re.search(l[1])]
    searchTag = [l for l in content if tagmap_re.search(l[1])]

    if len(searchCustomElement) > 1:
        print("Skipping {}, too many custom element declarations".format(fn))
        return

    if len(searchClass) > 1:
        print("Skipping {}, too many class declarations".format(fn))
        return

    if len(searchTag) > 0:
        print("Skipping {}, HTMLElementTagNameMap already present".format(fn))
        return

    if len(searchCustomElement) == 0:
        print("Skipping {}, no custom element found".format(fn))
        return

    if len(searchClass) == 0:
        print("Skipping {}, no class found after custom element?".format(fn))
        return

    if (searchCustomElement[0][0] + 1) != searchClass[0][0]:
        print("Skipping {}, customElement Declaration does not immediately precede class declaration".format(fn))
        return

    ceSearch = customElement_re.search(searchCustomElement[0][1]);
    clSearch = class_re.search(searchClass[0][1]);

    ceName = ceSearch.group(1)
    clName = clSearch.group(1)

    text = [l[1] for l in content]
    
    text.extend([
        "\n",
        "declare global {\n",
        "    interface HTMLElementTagNameMap {\n",
        '        "{}": {};\n'.format(ceName, clName),
        "    }\n",
        "}\n",
        "\n"
    ]);
    
    with open(fn, "w", encoding="utf-8") as elemfile:
        elemfile.write("".join(text))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("This requires a filename")
        sys.exit(-1)

    inject(sys.argv[1])

