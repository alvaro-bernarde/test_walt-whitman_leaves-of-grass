from bs4 import BeautifulSoup
from bs4.element import NavigableString
from pathlib import Path
import subprocess

root = Path(".").resolve()
output = root / "output"
source = root / "ppp.00707.xml"
body_output = output / "body.xhtml"
template = root / "template.xhtml"

soup = BeautifulSoup(source.read_text(), "xml")
soup = BeautifulSoup(str(soup.find_all("body")[2]), "xml")

# Remove Page Breaks
tags = soup.find_all("pb")
for tag in tags:
    tag.extract()

# Remove Relations
tags = soup.find_all("relations")
for tag in tags:
    tag.extract()

# Convert horizontal bars in <hr /> elements with appropriate class
tags = soup.find_all("milestone")
for tag in tags:
    tag.name = "hr"
    tag["class"] = tag["rend"]
    del tag["rend"], tag["unit"]

# Convert "clusters" into "sections"
tags = soup.find_all("lg", type="cluster")
for tag in tags:
    tag.name = "section"
    tag["epub:type"] = "part bodymatter"
    del tag["type"], tag["xml:id"]

# Convert "poems" into "articles"
tags = soup.find_all("lg", type="poem")
for tag in tags:
    tag.name = "article"
    tag["epub:type"] = "z3998:poem bodymatter"
    del tag["type"], tag["xml:id"]

# Convert "linegroups" into "p". Some errors in the source here. Reported to WWA already.
tags = soup.find_all("lg", type="linegroup")
tags += soup.find_all("lg", type="lingegroup")
tags += soup.find_all("lg")
for tag in tags:
    tag.name = "p"
    del tag["type"]

# Convert "sections" into "sections"
tags = soup.find_all("lg", type="section")
for tag in tags:
    tag.name = "section"
    del tag["type"]

# Sort out headings
tags = soup.find_all("head", type="main-authorial")
for tag in tags:
    parents = [parent.name for parent in tag.parents]
    h_level = parents.index("body") + 1
    tag.name = "h" + str(h_level)
    del tag["type"]
    tag["epub:type"] = "title"

# Sort out subheadings
tags = soup.find_all("head", type="sub")
for tag in tags:
    previous_sibling = tag.previous_sibling
    if not tag.previous_sibling.name:
        previous_sibling = previous_sibling.previous_sibling

    if previous_sibling.name in ["h2", "h3", "h4", "h5"]:

        h_level = int(previous_sibling.name[1]) + 1
        tag.name = "h" + str(h_level)
        del tag["type"]
        tag["epub:type"] = "subtitle"
        hgroup = [previous_sibling, tag]
        hgroup_tag = soup.new_tag("hgroup")
        previous_sibling.insert_before(hgroup_tag)
        hgroup_tag.extend(hgroup)
    else:
        print("Subheading without a heading")
        print(tag)

# Sout out lines
tags = soup.find_all("l")
for tag in tags:
    if tag.next_sibling:
        next_sibling = tag.next_sibling
        if not next_sibling.name and next_sibling.next_sibling:
            next_sibling = next_sibling.next_sibling
        if next_sibling.name == "l":
            br = soup.new_tag("br")
            tag.insert_after(br)

    tag.name = "span"

    if tag.has_attr("rend"):
        if tag["rend"] in ["indented1", "indented2", "indented3", "indented4"]:
            tag["class"] = "i" + tag["rend"][-1]
        elif tag["rend"] == "italic":
            tag.name = "i"
        del tag["rend"]

# Sort out italics
tags = soup.find_all("hi", rend="italic")
for tag in tags:
    tag.name = "i"
    del tag["rend"]

# Sort out small caps
tags = soup.find_all("hi", rend="smallcaps")
for tag in tags:
    previous = tag.previous_sibling
    if type(previous) == NavigableString:
        previous_str = str(previous)
        if len(previous_str) == 1:
            tag.string = previous_str + str(tag.string).lower()
        else:
            tag.string = previous_str + str(tag.string).lower()
        previous.extract()
        tag.name = "b"
        del tag["rend"]

# Sort out small caps
tags = soup.find_all("b", rend="smallcaps")
for tag in tags:
    previous = tag.previous_sibling
    if type(previous) == NavigableString:
        previous_str = str(previous)
        if len(previous_str) == 1:
            tag.string = previous_str + str(tag.string).lower()
        else:
            tag.string = previous_str + str(tag.string).lower()
        previous.extract()
        tag.name = "b"
        del tag["rend"]

tags = soup.find_all("lb")
for tag in tags:
    tag.extract()


# Save XML to ./dist
soup.body.unwrap()
template_soup = BeautifulSoup(template.read_text(), "xml")
template_soup.body.append(soup)
output.mkdir(exist_ok=True)
body_output.touch(exist_ok=True)
body_output.write_text(str(template_soup))
subprocess.run(["se", "clean", body_output])
