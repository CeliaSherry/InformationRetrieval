from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import json
from bs4 import BeautifulSoup
import pickle
import time

robots_dict = {}
outlinks_dict = {}
visited_dict = {}


# Stores links, the time they were found, and the number of inlinks
class Link:
    def __init__(self, link, count=1):
        self.link = link
        self.count = count
        self.time = time.time()

    def __eq__(self, other):
        return self.link == other.link

    def __lt__(self, other):
        return (self.count < other.count) or (self.count == other.count and self.time > other.time)

    def __gt__(self, other):
        return (self.count > other.count) or (self.count == other.count and other.time > self.time)

    def merge(self, other):
        self.count += 1


# Canonicalize URLs to use as IDs
def url_canonicalization(url, base=None):
    # Convert scheme and host to lowercase
    url = url.lower()
    if not url.startswith("http"):
        url = urljoin(base, url)
    # Remove port 80 from http URLs and port 443 from HTTPS URLs
    if url.startswith("http") and url.endswith(":80"):
        url = url[:-3]
    if url.startswith("https") and url.endswith(":443"):
        url = url[-4]
    # Remove the fragment after #
    url = url.rsplit('#', 1)[0]
    # Remove duplicate slashes
    stage = url.rsplit('://')
    deduped = stage[1].replace('//','/')
    url = stage[0] + '://' + deduped

    return url


# Check robots.txt for url.  Return true if allowed, false if not.
def check_robot(url):
    scheme, netloc, path, params, query, fragment = urlparse(url)
    robot_txt = scheme + "://" + netloc + "/robots.txt"
    try:
        if robot_txt not in robots_dict:
            rp = RobotFileParser()
            rp.set_url(robot_txt)
            rp.read()
            robots_dict[robot_txt] = rp
        r = robots_dict[robot_txt]
        return r.can_fetch("*", url)
    except Exception:
        return True


# Returns HTML from url, the <p> body of HTML, the <h> header of HTML, and the title of HTML
# Adds outlinks for page to outlinks dict
def parse_page(url, http_response, outlinks):
    outlinks = []

    raw = http_response.read()
    # Use BeautifulSoup to parse raw HTML
    soup = BeautifulSoup(raw, 'html.parser')
    header = ' '.join(http_response.info())

    # Page title
    title = soup.title.string

    # Page body
    body = [''.join(s.findAll(text=True)) for s in soup.findAll('p')]
    body = ' '.join(body)

    # Base url
    base = urlparse(url)[0] + '://' + urlparse(url)[1] + urlparse(url)[2]

    # Get outlinks
    for a in soup.find_all('a', href=True):
        link = url_canonicalization(a['href'], base)
        if ('javascript' not in link) and ('.pdf' not in link):
            frontier.insert(Link(link))
            outlinks.append(link)

    # Store outlinks
    outlinks_dict[url] = outlinks
    return raw, body, header, title








