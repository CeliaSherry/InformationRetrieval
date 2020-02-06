import dill
from collections import OrderedDict
from main import Term


def unpickler(file):
    f = open(file, 'rb')
    ds = dill.load(f)
    f.close()
    return ds


def parse_catalog(file):
    catalog = {}
    catalog_file = open(file, 'r')
    for line in catalog_file.readlines():
        text = line.strip().split(',')
        catalog[text[0]] = text[1:]
    return catalog


def get_files():
    term_map = unpickler('Files/Stemmed/Pickles/termMap.p')
    catalog = parse_catalog('Files/Stemmed/catalog_file.txt')
    doc_length = unpickler('Files/Stemmed/Pickles/lengthMap.p')
    doc_map = unpickler('Files/Stemmed/Pickles/docMap.p')
    avg_doc_length = sum(doc_length.values()) / len(doc_length)
    vocab = len(catalog.keys())
    return term_map, catalog, doc_length, doc_map, avg_doc_length, vocab


def term_api(term, catalog, term_map, doc_map):
    term_info = OrderedDict()
    inverted_list = OrderedDict()
    doc_dict = OrderedDict()

    # Open full index file
    index_file = open("Files/Stemmed/inverted_file0.txt", 'r')

    # Find offset and read line
    k = str(term_map[term])
    offset = catalog[k][0]
    index_file.seek(int(offset))
    line = index_file.readline()

    # Get DF (structured as [docId, DF, TTF] after colon)
    df = line.split(':')[0].split(',')[1]
    ttf = line.split(':')[0].split(',')[2]
    # Store in term info dictionary
    term_info[term] = [df, ttf]

    # Get inverted list for term- docs are separated by ; and structured (doc_num, tf, positions)
    s = line.split(':')[1].split(';')
    for d in s:
        doc_number = d.split(',')[0]
        # Use doc map dictionary to map document number to document id
        doc_id = doc_map.get(int(doc_number))
        tf = int(d.split(',')[1])
        positions = [int(e) for e in d.split(',')[2:len(d.split(','))]]
        doc_dict[doc_id] = Term(tf, positions)
    inverted_list[term] = doc_dict
    index_file.close()
    return inverted_list, term_info








def main():
    term_map, catalog, doc_length, doc_map, avg_doc_length, vocab = get_files()
