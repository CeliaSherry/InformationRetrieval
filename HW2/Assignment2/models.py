from main import Term
from queries import get_files
from queries import clean_queries
from queries import unpickler
from collections import defaultdict
from operator import itemgetter


# Get query numbers
def get_query_numbers():
    queries = clean_queries()
    numbers = []
    for query in queries:
        numbers.append(int(query.split()[0]))
    return numbers


# Restructure vector to not be Term class but to be dict of dicts
def restructure_vector(term_vector):
    dict_doc_id = defaultdict(lambda: defaultdict(list))
    for key in term_vector:
        for doc_id in term_vector[key]:
            dict_doc_id[doc_id][key] = [term_vector[key][doc_id].get_term_frequency(), term_vector[key][doc_id].get_position()]
    return dict_doc_id


def okapi_tf(query, term_vector, doc_info, avg_doc_length):
    doc_score = []
    doc_dict = restructure_vector(term_vector)
    for doc in doc_dict:
        tf = 0
        for key in doc_dict[doc]:
            tfwd = doc_dict[doc][key][0]
            length = int(doc_info.get(doc))
            tf += (tfwd / (tfwd + 0.5 + (1.5 * (length / avg_doc_length))))
        doc_score.append([doc, tf])
    doc_score.sort(key=itemgetter(1), reverse=True)
    with open('Files/Stemmed/Results/OkapiTF_Results_file.txt', 'a+') as results:
        rank = 1
        for ds in doc_score:
            results.write('%s Q0 %s %d %lf Exp\n' % (query, ds[0], rank, ds[1]))
            if rank == 1000:
                break
            rank += 1



def main():
    term_map, catalog, doc_length, doc_map, avg_doc_length, vocab = get_files()
    queries = get_query_numbers()
    for query in queries:
        term_stats = unpickler('Files/Stemmed/Pickles/termStats%s.p' % query)
        term_vector = unpickler('Files/Stemmed/Pickles/termVector%s.p' % query)
        okapi_tf(query, term_vector, doc_length, avg_doc_length)



main()


