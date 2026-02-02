from bs4 import BeautifulSoup
import argparse
import os
import re
import sys

invalid_links = []


def get_page_status(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "")).strip().lower()

    target_label = "page status"

    for tag in soup.find_all(["td", "th", "span", "div", "p", "b", "strong"]):
        if norm(tag.get_text(" ", strip=True)) == target_label:
            sib = tag.find_next_sibling(["td", "th", "span", "div", "p"])
            if sib:
                status = sib.get_text(" ", strip=True).strip()
                if status:
                    return status

            parent = tag.parent
            if parent:
                candidates = parent.find_all(["td", "th", "span", "div", "p"], recursive=True)
                for c in candidates:
                    txt = c.get_text(" ", strip=True).strip()
                    if txt and norm(txt) != target_label:
                        return txt

    body_text = soup.get_text("\n", strip=True)
    m = re.search(r"Page Status\s*[:\-]?\s*(.+)", body_text, flags=re.IGNORECASE)
    if m:
        status_line = m.group(1).strip()
        status_line = status_line.split("\n")[0].strip()
        return status_line if status_line else None

    return None


def extract_description(html_content, page_name):
    soup = BeautifulSoup(html_content, "html.parser")

    description_header = soup.find("h2", string="Description")
    if description_header:
        description_elements = []
        next_element = description_header.find_next_sibling()
        encountered_headings = set()

        while next_element and next_element.name != "div":
            if next_element.name in ["p", "ul", "li", "div", "b", "h2"]:
                for sup in next_element.find_all("sup"):
                    sup.insert_before(" ")
                    sup.decompose()

                if next_element.find("a"):
                    links = next_element.find_all("a", href=True)
                    for link in links:
                        link_text = link.get_text(strip=True)
                        link_url = link["href"]

                        if link_text == link_url:
                            invalid_links.append(
                                (page_name, link_text, link_url, "Description", "Link Name URL Match")
                            )

                        if not re.search(r"(http|https)://", link_url):
                            invalid_links.append(
                                (page_name, link_text, link_url, "Description", "Local or Internal File")
                            )
                            link.replace_with(link_text)
                        else:
                            formatted_link = f"{link_text}:{link_url}" if link_text != link_url else link_url
                            link.replace_with(formatted_link)

                if next_element.name == "h2" and next_element.string in [
                    "Background/Context",
                    "Method",
                    "Limitations",
                ]:
                    if next_element.string not in encountered_headings:
                        description_elements.append(next_element.get_text(" ", strip=True))
                        encountered_headings.add(next_element.string)
                else:
                    text = next_element.get_text(" ", strip=True)
                    if text:
                        description_elements.append(text)

            next_element = next_element.find_next_sibling()

        description_text = " ".join(description_elements)
        return description_text.strip()

    return "Placeholder"


def extract_resources(html_content, page_name):
    soup = BeautifulSoup(html_content, "html.parser")

    resource_links = []
    headings = soup.find_all(
        re.compile(r"^h[2-3]$"),
        string=re.compile(r"Definition\sLogic|Related\sCodesets|References", re.IGNORECASE),
    )

    for heading in headings:
        next_sibling = heading.find_next_sibling()
        while next_sibling and next_sibling.name != "h2" and next_sibling != headings[-1]:
            if next_sibling.name == "p":
                links = next_sibling.find_all("a", href=True)
                for link in links:
                    link_text = link.get_text(strip=True).replace(":", "")
                    link_url = link["href"]

                    if link_text == link_url:
                        invalid_links.append(
                            (page_name, link_text, link_url, "Resources", "Link Name URL Match")
                        )

                    if re.search(r"(http|https)://", link_url):
                        resource_links.append((heading.get_text(), link_text, link_url))
                    else:
                        invalid_links.append(
                            (page_name, link_text, link_url, "Resources", "Local or Internal File")
                        )
                        resource_links.append((heading.get_text(), link_text, ""))

            next_sibling = next_sibling.find_next_sibling()

    formatted_links = []
    for heading, name, href in resource_links:
        if href != "":
            formatted_link = f'"{heading} - {name}":{href}'
        else:
            formatted_link = f'"{heading} - {name}":"https://www.google.com/"'
        formatted_links.append(formatted_link)

    return ";".join(formatted_links)


FINAL_STATUS = "confluence page finalized"


def run_scraper(directory, output_file, invalid_file):
    global invalid_links
    invalid_links = []

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(
            '"Nick Name","Name","Definition","IsDefinitionRichText","Status","Related Terms","Synonyms","Acronym","Experts","Stewards","Resources","Parent Term Name","Term Template Names"\n'
        )

        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)

            if os.path.isfile(f):
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()

                page_status = get_page_status(content)
                if not page_status or page_status.strip().lower() != FINAL_STATUS:
                    continue

                full_name_element = BeautifulSoup(content, "html.parser").find("span", id="title-text")
                if not full_name_element:
                    continue

                full_name = full_name_element.get_text().strip()
                name = full_name.replace("Concept Definitions :", "").strip()

                acronym = ""
                m = re.search(r"\(([A-Z]+)\)", name)
                if m:
                    acronym = m.group(1)

                name = re.sub(r"\n", "", name)
                name = re.sub(r"\.", "", name)
                name = re.sub(r"@", "", name)

                description = extract_description(content, name)
                description = description.replace('"', '""')
                description = re.sub(r"\n", "", description)
                description = re.sub(r"\s+", " ", description)

                resources = extract_resources(content, name)
                resources = resources.replace('"', "")
                resources = re.sub(r"\n", "", resources)
                resources = re.sub(r"\s+", " ", resources)

                out.write(
                    f'"{name}","","{description}","true","Draft","","","{acronym}","","","{resources}","","System Default;"\n'
                )

    with open(invalid_file, "w", encoding="utf-8") as out:
        out.write('"Page Name","Link Text","URL","Location","Issue"\n')
        for pagename, linkText, link, location, issue in invalid_links:
            out.write(f'"{pagename}","{linkText}","{link}","{location}","{issue}"\n')


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Confluence export HTML into CSV.")
    parser.add_argument(
        "--input",
        default=r"C:\Users\justin\Downloads\Confluence-space-export-220712.html\CD",
        help="Folder containing Confluence HTML files.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.expanduser("~"), "Desktop", "scraped-finalized-definitionsv2.csv"),
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--invalid",
        default=os.path.join(os.path.expanduser("~"), "Desktop", "invalid-links.csv"),
        help="Invalid links CSV file path.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_scraper(args.input, args.output, args.invalid)
