from main import Term
from queries import get_files
from queries import clean_queries
from queries import unpickler
from collections import defaultdict
from operator import itemgetter
import math


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


def window_range(positions):
    min_range = float("inf")
    word_positions = {}
    # Beginning of algorithm- initially starts at beginning of each list
    for word in positions:
        # Get position of first time word appears
        word_positions[word] = positions[word][0]
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
            word_positions.pop(smallest_word)
        # Check if range is smaller than minimum range.  Replace if so.
        if current_range < min_range:
            min_range = current_range
    return min_range


def proximity(query, term_vector, doc_info, vocab):
    doc_score = []
    doc_dict = restructure_vector(term_vector)
    positions = {}
    c = 1500
    for doc_id in doc_dict:
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
    doc_score.sort(key=itemgetter(1), reverse=True)
    with open('Files/Stemmed/Results/proximity.txt', 'a+') as results:
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
        term_stats = unpickler('Files/Stemmed/Pickles/termStatsProximity%s.p' % query)
        term_vector = unpickler('Files/Stemmed/Pickles/termVectorProximity%s.p' % query)
        proximity(query, term_vector, doc_length, vocab)


#main()


