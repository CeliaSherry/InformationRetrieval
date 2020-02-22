from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import json
from bs4 import BeautifulSoup
import pickle
import time
import urllib.request
from frontier import MinHeap, QueueLink

robots_dict = {}
outlinks_dict = {}
queue = {}
visited_set = set()
frontier = MinHeap()


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
    if len(stage) > 1:
        deduped = stage[1].replace('//','/')
        url = stage[0] + '://' + deduped
    else:
        url = url.replace('//','/')

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
def parse_page(url, http_response):
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
            outlinks.append(link)
            outlinks_dict[link] = outlinks
            if link not in visited_set:
                try:
                    queue[link].add_inlinks(1)
                except KeyError:
                    new_element = QueueLink(link, 1)
                    queue[link] = new_element
                    frontier.insert(new_element)

    return raw, body, header, title, outlinks


# Writes cleaned HTML to file.  Will be able to reuse code from Assignments 1 and 2.
def write_to_file(body, header, title, url, file_name):
    f = open(file_name, "w")
    text = '<DOC><DOCNO>' + url + '</DOCNO><HEADER>' + header + '</HEADER><TITLE>' + title + '</TITLE><TEXT>' + body + '</TEXT></DOC>'
    f.write(text)
    f.close()


# Write outlinks for url to file
def dump_outlinks():
    f = open('./Pickles/outlinks','w')
    json.dump(outlinks_dict, f)
    f.close()


# Crawl URLs in frontier
def crawl(frontier, limit=10):
    crawled_count = 0
    while crawled_count < limit:
        start_time = time.time()
        next_link = frontier.pop()
        url = next_link.link
        queue.pop(url)


        # If URL has been visited or not allowed to be crawled by robot.txt, skip
        if url in visited_set or not check_robot(url):
            continue
        visited_set.add(url)
        time1 = time.time()
        time2 = None
        time3 = None
        time4 = None
        parse_time = 0
        store_time = 0
        try:
            print("Crawling {0}".format(url))
            time1 = time.time()
            with urllib.request.urlopen(url, timeout=5) as resp:
                time2 = time.time()
                raw, body, header, title, outlinks = parse_page(url, resp)
                # Move to parse page function so you only have to go through once
                #outlinks_dict[url] = outlinks
                #for link in outlinks:
                #    if link not in visited_set:
                #        try:
                #            queue[link].add_inlinks(1)
                #        except KeyError:
                #            new_element = QueueLink(link, 1)
                #            queue[link] = new_element
                #            frontier.insert(new_element)

                time3 = time.time()
                write_to_file(body, header, title, url, './Files/content-{0}.txt'.format(crawled_count))
                time4 = time.time()
                request_time = time2-time1
                parse_time = time3-time2
                store_time = time4-time3
                crawled_count += 1
                frontier.heapify()
        except Exception as e:
            print(e)
            continue

        s = parse_time + store_time + request_time
        print(s)

        # Politeness: if 1 second hasn't passed from last request, sleep remaining time
        if s <= 1:
            time.sleep(1-s)

        # Dump frontier and visited dicts every 100 files so don't need to start from beginning in case of crash
        if (crawled_count % 100) == 0:
            frontier_output = open('./Pickles/frontier', 'wb')
            visited_output = open('./Pickles/visited', 'wb')
            pickle.dump(frontier, frontier_output)
            pickle.dump(visited_set, visited_output)
            frontier_output.close()
            visited_output.close()
            # dump all outlinks
            dump_outlinks()


def main():
    seed_urls = [
        'http://www.history.com/topics/world-war-ii',
        'http://en.wikipedia.org/wiki/World_War_II',
        'http://www.history.com/topics/world-war-ii/battle-of-stalingrad',
        'http://en.wikipedia.org/wiki/Battle_of_Stalingrad'
        #,'https://www.google.com/search?client=safari&rls=en&q=battle+of+stalingrad&ie=UTF-8&oe=UTF-8'
    ]
    #frontier = MinHeap()
    for url in seed_urls:
        new_node = QueueLink(url, 1000000)
        queue[url] = new_node
        frontier.insert(new_node)

    crawl(frontier)



main()








# UPDATE LIMIT IN CRAWL
# CREATE FRONTIER
# LOAD FRONTIER/RESTART



