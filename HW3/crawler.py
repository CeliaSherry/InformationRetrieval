from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import json

robots_dict = {}


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
def parse_page(url, http_response, outlinks):





