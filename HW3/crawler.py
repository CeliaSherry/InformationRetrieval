from urllib.parse import urlparse, urljoin


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



