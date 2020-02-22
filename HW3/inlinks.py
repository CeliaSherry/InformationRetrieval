import pickle
from bs4 import BeautifulSoup


inlinks_dict = {}

def load_outlinks():
    outlinks_file = open("Pickles/outlinks", "rb")
    outlinks = pickle.load(outlinks_file)
    outlinks_file.close()
    return outlinks


def get_docs(file):
    f = file.read()
    page = "<root>" + f + "</root>"
    soup = BeautifulSoup(page, features='xml')
    return soup.find_all('DOC')


def dump_inlinks():
    inlinks_file = open("Pickles/inlinks", "wb")
    pickle.dump(inlinks_dict, inlinks_file)
    inlinks_file.close()


def get_inlinks():
    outlinks = load_outlinks()

    f = open("Files/content.txt", "r")
    documents = get_docs(f)
    for document in documents:
        inlinks = []
        doc_id = document.find('DOCNO').get_text().strip()

        for key in outlinks:
            if doc_id in outlinks[key]:
                inlinks.append(key)
        inlinks_dict[doc_id] = inlinks
    dump_inlinks()


