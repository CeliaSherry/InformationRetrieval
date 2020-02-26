import pickle
from bs4 import BeautifulSoup
import re


inlinks_dict = {}


def load_outlinks():
    outlinks_file = open("Pickles/outlinks", "rb")
    outlinks = pickle.load(outlinks_file)
    outlinks_file.close()
    return outlinks


def get_docs():
    doc_regex = re.compile('<DOC>.*?</DOC>', re.DOTALL)
    f = open("Files/content.txt", "r")
    contents = f.read()
    documents = re.findall(doc_regex, contents)
    return documents


def dump_inlinks():
    inlinks_file = open("Pickles/inlinks", "wb")
    pickle.dump(inlinks_dict, inlinks_file)
    inlinks_file.close()


def get_inlinks():
    docno_regex = re.compile('<DOCNO>.*?</DOCNO>', re.DOTALL)
    outlinks = load_outlinks()

    documents = get_docs()
    count = 1
    for document in documents:
        print(count)
        count += 1
        inlinks = []
        doc_id = ''.join(re.findall(docno_regex, document)).replace('<DOCNO>', '').replace('</DOCNO>', '')

        for key in outlinks:
            if doc_id in outlinks[key]:
                inlinks.append(key)
        inlinks_dict[doc_id] = inlinks
    dump_inlinks()


get_inlinks()
