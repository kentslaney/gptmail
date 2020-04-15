import urllib.request, urllib.parse, re, html
from tqdm import tqdm

article_urls = re.compile(rb"""<a [^>]*href=["']([^'"]+\.art\.(html|php))""")
article_text = re.compile(r"<p(?: [^>]*?)?>([^<].*?)</p>", re.DOTALL)
non_content = re.compile(r"</?[a-z]+(?: [^>]*)?>")
index_urls = [
    "https://scripts.mit.edu/~hwtaylor/xc/xcsched.php",
    "https://scripts.mit.edu/~hwtaylor/xc/pastseasons.php",
]

def scrape_index(url):
    res = urllib.request.urlopen(url).read()
    urls = [[j.decode('utf-8') for j in i.groups()] for i in article_urls.finditer(res)]
    return [(urllib.parse.urljoin(url, rel), ext) for rel, ext in urls]

def scrape_article(url, article_type):
    res = urllib.request.urlopen(url).read().decode("utf-8")
    if article_type == "html" or article_type == "php":
        return "\n\n".join(html.unescape(non_content.sub("", i))
            for i in article_text.findall(res))
    else:
        raise Exception("unknown article type")

if __name__ == "__main__":
    import os, argparse, shutil
    relpath = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)
    parser = argparse.ArgumentParser(description="clean up eml files")
    parser.add_argument("--output", default=relpath("..", "..", "add"))
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--no-overwrite", dest="overwrite", action="store_false")
    group.add_argument("--overwrite", dest="overwrite", action="store_true")
    parser.set_defaults(overwrite=True)
    args = parser.parse_args()

    if args.overwrite:
        shutil.rmtree(args.output, True)
        os.mkdir(args.output)

    urls = sum((scrape_index(i) for i in index_urls), [])
    for i, (url, article_type) in enumerate(tqdm(urls)):
        with open(os.path.join(args.output, "article{}".format(i)), "w+") as fp:
            fp.write(scrape_article(url, article_type))
