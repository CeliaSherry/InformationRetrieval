from queries_unstemmed import get_files
from queries_unstemmed import clean_queries
from queries_unstemmed import unpickler
from collections import defaultdict
from operator import itemgetter
from collections import OrderedDict
import dill
import re
from nltk.stem import PorterStemmer
from queries_unstemmed import get_keywords, term_api
from string import digits


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
            t = list(set(term_vector[key][doc_id].get_position()))
            t.sort()
            dict_doc_id[doc_id][key] = [len(t),t]
    return dict_doc_id


def closest_two(l):
    i = 1
    current_min = float("inf")
    while i < len(l):
        m = l[i] - l[i-1]
        if m < current_min:
            current_min = m
        i += 1
    return current_min


def window_range(positions):
    min_range = float("inf")
    word_positions = {}
    # Beginning of algorithm- initially starts at beginning of each list
    for word in positions:
        # Get position of first time word appears
        word_positions[word] = positions[word][0]
    if len(word_positions) == 1:
        m = closest_two(positions[word])
        return m
        #l = len(positions[word]) - 1
        #return positions[word][l] - positions[word][0]
    max_len = len(word_positions)
    while max_len == len(word_positions):
        # Find range of interval
        current_range = word_positions.get(max(word_positions, key=word_positions.get)) - word_positions.get(min(word_positions, key=word_positions.get))
        # Find word with smallest position
        smallest_word = min(word_positions, key=word_positions.get)
        # Find position of smallest word
        min_pos = positions[smallest_word].index(word_positions.get(smallest_word))
        # If there are more positions in the list
        if min_pos < (len(positions[smallest_word]) - 1):
            # Move position forward one
            new_pos = positions[smallest_word][min_pos + 1]
            word_positions[smallest_word] = new_pos
        else:
            #print(smallest_word)
            word_positions.pop(smallest_word)
        # Check if range is smaller than minimum range.  Replace if so.
        if current_range < min_range:
            min_range = current_range
    return min_range


def proximity(query, term_vector, doc_info, vocab):
    doc_score = []
    doc_dict = restructure_vector(term_vector)
    positions = {}
    c = 15000
    num_docs = 1
    for doc_id in doc_dict:
        #print(str(num_docs) + ' out of ' + str(len(doc_dict)))
        #print(doc_id)
        num_docs += 1
        i = 0
        length = int(doc_info.get(doc_id))
        for word in doc_dict[doc_id]:
            positions[word] = doc_dict[doc_id][word][1]
            # Keep track of number of words in document from query
            i += 1
        # positions is dict with query words and keys are list of positions
        smallest_range = window_range(positions)
        score = (c - smallest_range) * i / (length + vocab)
        doc_score.append([doc_id, score])
        if doc_id == 'AP891016-0226':
            print(score)
    doc_score.sort(key=itemgetter(1), reverse=True)
    with open('Files/Unstemmed/Results/proximity.txt', 'a+') as results:
        rank = 1
        for ds in doc_score:
            results.write('%s Q0 %s %d %lf Exp\n' % (query, ds[0], rank, ds[1]))
            if rank == 1000:
                break
            rank += 1


def get_queries():
    f = open('AP_DATA/queries.txt', 'r')
    new_queries = []
    for line in f:
        line = line.replace("'", " ")
        line = line.replace(",", " ")
        line = line.replace("-", " ")
        line = line.replace("(", "")
        line = line.replace(")", "")
        new_queries.append(re.sub('[\-\.\"\s]+', ' ', line).strip().translate(digits))
    return new_queries


# Gets inverted list for queries and pickles them
def get_query_vectors(query, catalog, term_map, doc_map):
    query_num = int(query.split()[0])
    term_vector = OrderedDict()
    keywords = get_keywords(query.split()[1:])
    for key in keywords:
        #key = stemmer.stem(key).lower()
        key = key.lower()
        inverted_list, term_info = term_api(key, catalog, term_map, doc_map)
        term_vector.update(inverted_list)
    f = open('Files/Unstemmed/Pickles/termVectorProximity%s.p' % query_num, 'wb')
    dill.dump(term_vector, f)
    f.close()


def queries():
    term_map, catalog, doc_length, doc_map, avg_doc_length, vocab = get_files()
    new_queries = get_queries()
    q_num = 0
    for query in new_queries:
        q_num += 1
        get_query_vectors(query, catalog, term_map, doc_map)
        print("Created %d vector" % q_num)



def main():
    term_map, catalog, doc_length, doc_map, avg_doc_length, vocab = get_files()
    query_nums = get_query_numbers()
    for query in query_nums:
    #query = 80
        term_vector = unpickler('Files/Unstemmed/Pickles/termVectorProximity%s.p' % query)
        print('Running %s query' % query)
        proximity(query, term_vector, doc_length, vocab)


#stemmer = PorterStemmer()
#queries()
#main()


