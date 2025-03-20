import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

def write_list_to_file(outpath: Path, data):
    supported_file_extensions = [".txt", ".json"]
    if outpath.suffix not in supported_file_extensions: 
        raise ValueError(
            f"""{outpath} has unsupported file extension: {outpath.suffix}. \n
            Supported file extensions include: {supported_file_extensions}
            """
        )
    with outpath.open(mode="w", encoding="utf-8") as file:
        if outpath.suffix == ".txt":
            file.writelines(f"{ele}\n" for ele in data)
        elif outpath.suffix == ".json":
            json.dump(data, file, indent=4, ensure_ascii=False)

def read_list_from_file(inpath: Path) -> list[str]:
    with inpath.open(mode="r", encoding="utf-8") as file:
        slist = file.readlines()
        slist = [ele.strip() for ele in slist]
        return slist
def extract_data_from_seriouseats(soup: BeautifulSoup):
    # extracting main content 
    head = soup.select_one('head.loc.head')
    json_content = None
    if head: 
        json_ld_tag = head.find('script', type="application/ld+json")
        if json_ld_tag:
            json_content = json.loads(json_ld_tag.string)
            return json_content
    
    # **Originally intended to 
    # if json_content:
    #     for content in json_content:
    #         recipe = {
    #             "recipe_name": content["headline"],
    #             "recipe_authors": [],
    #             "recipe_description": content["description"],
    #             ""

    #         }

def main():
    """
    Currently using simple filtering of sitemap urls by looking if they end with -recipe
    A better way to do this is checking for @Type: Recipe in HTML>
    """
    # XML Sitemap of SeriousEats
    sitemap_url = "https://www.seriouseats.com/sitemap_1.xml"
    urls_filename = "recipe_urls.txt"
    urls_fp = Path(urls_filename)
    recipe_data_filename = "recipes_dump.json"
    recipe_data_fp = Path(recipe_data_filename)

    print("Retrieving urls from sitemap...")
    if not urls_fp.exists():
        r = requests.get(sitemap_url)
        r.raise_for_status()
        xml = r.text
        soup = BeautifulSoup(markup=xml, features="xml")
        sitemap_tags = soup.find_all("loc")
        recipe_urls = [loc.text for loc in sitemap_tags if loc.text.endswith('-recipe')]
        write_list_to_file(urls_fp, recipe_urls)
    else:
        recipe_urls = read_list_from_file(urls_fp)

    print("Scraping content from each website...")
    recipe_jsons = []

    # TODO: This needs to be loaded lazily in the future
    # As soon as the content is fetched from the website, write it to file

    for idx, url in enumerate(recipe_urls): 
        webpage = requests.get(url)
        webpage.raise_for_status()
        html = webpage.text
        webpage_soup = BeautifulSoup(markup=html, features="html.parser")
        recipe_json = extract_data_from_seriouseats(webpage_soup)

        # Would it be cleaner to explicitly say that I am checking for None?
        if recipe_json: 
            recipe_jsons.append(recipe_json)
        print(f"({idx} / {len(recipe_urls)}) scraped.")
    write_list_to_file(recipe_data_fp, recipe_jsons)

if __name__ == "__main__":
    main()