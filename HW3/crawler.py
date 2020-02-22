from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import pickle
import time
import urllib.request
from frontier import MinHeap, QueueLink


class Crawler:
    def __init__(self, outlinks_dict={}, queue={}, visited_set=set(), frontier=MinHeap(), robots_dict={}):
        self.outlinks_dict = outlinks_dict
        self.queue = queue
        self.visited_set = visited_set
        self.frontier = frontier
        self.robots_dict = robots_dict

    # Canonicalize URLs to use as IDs
    def url_canonicalization(self, url, base=None):
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
    def check_robot(self, url):
        scheme, netloc, path, params, query, fragment = urlparse(url)
        robot_txt = scheme + "://" + netloc + "/robots.txt"
        try:
            if robot_txt not in self.robots_dict:
                rp = RobotFileParser()
                rp.set_url(robot_txt)
                rp.read()
                self.robots_dict[robot_txt] = rp
            r = self.robots_dict[robot_txt]
            return r.can_fetch("*", url)
        except Exception:
            return True

    # Returns HTML from url, the <p> body of HTML, the <h> header of HTML, and the title of HTML
    # Adds outlinks for page to outlinks dict
    def parse_page(self, url, http_response):
        outlinks = set()

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
            link = self.url_canonicalization(a['href'], base)
            if ('javascript' not in link) and ('.pdf' not in link):
                outlinks.add(link)
                if link not in self.visited_set:
                    try:
                        if link.__contains__('world-war-ii') or link.__contains__('stalingrad'):
                            self.queue[link].add_inlinks(20)
                        else:
                            self.queue[link].add_inlinks(1)
                    except KeyError:
                        if link.__contains__('world-war-ii') or link.__contains__('stalingrad'):
                            new_element = QueueLink(link, 20)
                        else:
                            new_element = QueueLink(link, 1)
                        self.queue[link] = new_element
                        self.frontier.insert(new_element)
        self.outlinks_dict[url] = outlinks

        return raw, body, header, title, outlinks

    # Writes cleaned HTML to file.  Will be able to reuse code from Assignments 1 and 2.
    def write_to_file(self, raw, body, header, title, url, file_name):
        f = open(file_name, "a+")
        #text = '<DOC><DOCNO>' + url + '</DOCNO><HEADER>' + header + '</HEADER><TITLE>' + title + '</TITLE><TEXT>' + body + \
        #       '</TEXT>' + '<CONTENT>' + raw.decode('utf-8') + '</CONTENT></DOC>\n'
        text = '<DOC><DOCNO>' + url + '</DOCNO><HEADER>' + header + '</HEADER><TITLE>' + title + '</TITLE><TEXT>' + body + \
               '</TEXT></DOC>\n'
        f.write(text)
        f.close()

    # Crawl URLs in frontier
    def crawl(self, limit=10, crawled_count=0):
        while crawled_count < limit:
            start_time = time.time()
            next_link = self.frontier.pop()
            url = next_link.link
            self.queue.pop(url)


            # If URL has been visited or not allowed to be crawled by robot.txt, skip
            if url in self.visited_set or not self.check_robot(url):
                continue
            self.visited_set.add(url)
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
                    raw, body, header, title, outlinks = self.parse_page(url, resp)
                    time3 = time.time()
                    self.write_to_file(raw, body, header, title, url, './Files/content.txt')
                    time4 = time.time()
                    request_time = time2-time1
                    parse_time = time3-time2
                    store_time = time4-time3
                    crawled_count += 1
                    self.frontier.heapify()
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
                crawled_count_output = open('./Pickles/crawled_count','wb')
                pickle.dump(self.frontier, frontier_output)
                pickle.dump(self.visited_set, visited_output)
                pickle.dump(crawled_count, crawled_count_output)
                frontier_output.close()
                visited_output.close()
                crawled_count_output.close()
                # dump all outlinks
                outlinks_output = open('./Pickles/outlinks', 'wb')
                pickle.dump(self.outlinks_dict, outlinks_output)
                outlinks_output.close()
                # dump queue
                queue_output = open('./Pickles/queue', 'wb')
                pickle.dump(self.queue, queue_output)
                queue_output.close()


    def main(self):
        seed_urls = [
            'http://www.history.com/topics/world-war-ii',
            'http://en.wikipedia.org/wiki/World_War_II',
            'http://www.history.com/topics/world-war-ii/battle-of-stalingrad',
            'http://en.wikipedia.org/wiki/Battle_of_Stalingrad'
            #,'https://www.google.com/search?client=safari&rls=en&q=battle+of+stalingrad&ie=UTF-8&oe=UTF-8'
        ]
        for url in seed_urls:
            new_node = QueueLink(url, 1000000)
            self.queue[url] = new_node
            self.frontier.insert(new_node)

        self.crawl()


def load_frontier():
    crawled_count_file = open("Pickles/crawled_count","rb")
    frontier_file = open("Pickles/frontier", "rb")
    visited_file = open("Pickles/visited", "rb")
    outlinks_file = open("Pickles/outlinks", "rb")
    queue_file = open("Pickles/queue", "rb")
    crawled_count = pickle.load(crawled_count_file)
    frontier = pickle.load(frontier_file)
    visited = pickle.load(visited_file)
    outlinks = pickle.load(outlinks_file)
    queue = pickle.load(queue_file)
    crawled_count_file.close()
    frontier_file.close()
    visited_file.close()
    outlinks_file.close()
    queue_file.close()
    return outlinks, queue, visited, frontier, crawled_count


#crawler = Crawler()
#crawler.main()

#outlinks, queue, visited, frontier, crawled_count = load_frontier()
#crawler_restart = Crawler(outlinks, queue, visited, frontier)
#crawler_restart.crawl(limit=10, crawled_count=crawled_count)








# UPDATE LIMIT IN CRAWL
# LOAD FRONTIER/RESTART
# HOW TO MERGE ES
# DON'T HAVE INLINKS/OUTLINKS BE SAME PAGE



