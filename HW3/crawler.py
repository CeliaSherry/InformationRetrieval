from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import pickle
import time
import urllib.request
from frontier import MinHeap, QueueLink


blacklist_urls = [
    'http://en.wikipedia.org/wiki/International_Standard_Book_Number',
    'http://en.wikipedia.org/wiki/JSTOR',
    'http://en.wikipedia.org/wiki/Digital_object_identifier',
    'http://en.wikipedia.org/wiki/Cambridge_University_Press'
]


class Crawler:
    def __init__(self, outlinks_dict={}, queue={}, visited_set=set(), frontier=MinHeap(), robots_dict={}):
        self.outlinks_dict = outlinks_dict
        self.queue = queue
        self.visited_set = visited_set
        self.frontier = frontier
        self.robots_dict = robots_dict
        for url in blacklist_urls:
            self.visited_set.add(url)
        keywords = ["world", 'war', "ii", "ww2", "wwii", "stalingrad", "united",
                    "states", "nazi", "germany", "japan", "battles", "wwtwo", "worldwar2"]
        self.keywords = set(keywords)

    # Canonicalize URLs to use as IDs
    def url_canonicalization(self, url, base=None):
        if base is not None and not url.startswith("http"):
            url = urljoin(base, url)
        parse = urlparse(url)
        output = ''
        output += parse.scheme.lower() + "://"
        output += self.clean_domain(parse.netloc.lower(), parse.scheme.lower())
        if len(parse.path) > 0:
            output += self.clean_path(parse.path)
        return output

    def clean_path(self, p):
        comps = p.split('/')
        output = ''
        for cmp in comps:

            if len(cmp) > 0 and cmp != '/':
                output += '/' + cmp

        return output

    def clean_domain(self, domain, scheme):
        if scheme == 'http':
            if domain.endswith(':80'):
                return domain[:-len(':80')]
        elif scheme == 'https':
            if domain.endswith(':443'):
                return domain[:-len(':443')]
        return domain

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
            if ('javascript' not in link) and ('.pdf' not in link) and ('video' not in link) and ('jpeg' not in link):
                outlinks.add(link)
                if (link not in self.visited_set) and (link != url):
                    try:
                        if any(substring in link.lower() for substring in self.keywords):
                            self.queue[link].add_inlinks(20)
                        else:
                            self.queue[link].add_inlinks(1)
                    except KeyError:
                        if any(substring in link.lower() for substring in self.keywords):
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
        # text = '<DOC><DOCNO>' + url + '</DOCNO><HEADER>' + header + '</HEADER><TITLE>' + title + '</TITLE><TEXT>' + body + \
        #       '</TEXT>' + '<CONTENT>' + raw.decode('utf-8') + '</CONTENT></DOC>\n'
        text = '<DOC><DOCNO>' + url + '</DOCNO><HEADER>' + header + '</HEADER><TITLE>' + title + '</TITLE><TEXT>' + body + \
               '</TEXT></DOC>\n'
        f.write(text)
        f.close()

    # Crawl URLs in frontier
    def crawl(self, limit=40000, crawled_count=0):
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
            print(crawled_count)

            # Politeness: if 1 second hasn't passed from last request, sleep remaining time
            if s <= 1:
                time.sleep(1-s)

            # Dump frontier and visited dicts every 100 files so don't need to start from beginning in case of crash
            if (crawled_count % 100) == 0:
                frontier_output = open('./Pickles/frontier', 'wb')
                visited_output = open('./Pickles/visited', 'wb')
                crawled_count_output = open('./Pickles/crawled_count', 'wb')
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
            'http://en.wikipedia.org/wiki/Battle_of_Stalingrad',
            'https://www.britannica.com/event/battle-of-stalingrad',
            'https://www.britannica.com/event/world-war-ii',
            'http://www.bbc.co.uk/history/worldwars/wwtwo/',
            'https://time.com/tag/world-war-ii/'
            # 'https://www.historyplace.com/worldwar2/timeline/ww2time.htm'
            # ,'https://www.google.com/search?client=safari&rls=en&q=battle+of+stalingrad&ie=UTF-8&oe=UTF-8'
        ]
        for url in seed_urls:
            new_node = QueueLink(url, 1000000)
            self.queue[url] = new_node
            self.frontier.insert(new_node)

        self.crawl()


def load_frontier():
    crawled_count_file = open("Pickles/crawled_count", "rb")
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


crawler = Crawler()
crawler.main()

#outlinks, queue, visited, frontier, crawled_count = load_frontier()
#crawler_restart = Crawler(outlinks, queue, visited, frontier)
#crawler_restart.crawl(limit=10, crawled_count=crawled_count)


# HOW TO MERGE ES

# exclude spanish wikipedia
# may be repeats
