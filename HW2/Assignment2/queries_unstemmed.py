import dill
from collections import OrderedDict
from main import Term, get_stopwords
from string import digits
import re


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
    term_map = unpickler('Files/Unstemmed/Pickles/termMap.p')
    catalog = parse_catalog('Files/Unstemmed/catalog_file.txt')
    doc_length = unpickler('Files/Unstemmed/Pickles/lengthMap.p')
    doc_map = unpickler('Files/Unstemmed/Pickles/docMap.p')
    avg_doc_length = sum(doc_length.values()) / len(doc_length)
    vocab = len(catalog.keys())
    return term_map, catalog, doc_length, doc_map, avg_doc_length, vocab


def term_api(term, catalog, term_map, doc_map):
    term_info = OrderedDict()
    inverted_list = OrderedDict()
    doc_dict = OrderedDict()

    # Open full index file
    index_file = open("Files/Unstemmed/inverted_file0.txt", 'r')

    # Find offset and read line
    if term in term_map:
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


def clean_queries():
    f = open('AP_DATA/queries.txt', 'r')
    queries = []
    for line in f:
        line = line.replace("'", " ")
        queries.append(re.sub('[\-\.\"\s]+', ' ', line).strip().translate(digits))
    return queries


def get_keywords(query):
    stopwords = get_stopwords()
    keywords = []
    for word in query:
        if word not in stopwords:
            keywords.append(word)
    return keywords


# Gets inverted list for queries and pickles them
def get_query_vectors(query, catalog, term_map, doc_map):
    query_num = int(query.split()[0])
    term_vector = OrderedDict()
    term_stats = OrderedDict()
    keywords = get_keywords(query.split()[1:])
    for key in keywords:
        #key = stemmer.stem(key).lower()
        key = key.lower()
        inverted_list, term_info = term_api(key, catalog, term_map, doc_map)
        term_vector.update(inverted_list)
        term_stats.update(term_info)
    f = open('Files/Unstemmed/Pickles/termStats%s.p' % query_num, 'wb')
    dill.dump(term_stats, f)
    f.close()
    f = open('Files/Unstemmed/Pickles/termVector%s.p' % query_num, 'wb')
    dill.dump(term_vector, f)
    f.close()




def main():
    term_map, catalog, doc_length, doc_map, avg_doc_length, vocab = get_files()
    queries = clean_queries()
    q_num = 0
    for query in queries:
        q_num += 1
        get_query_vectors(query, catalog, term_map, doc_map)
        print("Created %d vector" % q_num)


    #inverted_list, term_info = term_api('govern', catalog, term_map, doc_map)
    #print(term_info)

#main()

