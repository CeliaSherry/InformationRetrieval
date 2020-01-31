from bs4 import BeautifulSoup
import regex
import re
import os
from nltk.stem import PorterStemmer
from collections import defaultdict
from collections import OrderedDict
import dill


# Store term frequency and term position
class Term:
    def __init__(self, tf, position):
        self.tf = tf
        self.position = position

    def get_term_frequency(self):
        return self.tf

    def get_position(self):
        return self.position


# Store terms, map of term id to term, file names that contain term, offset, and length
class Catalog:
    def __init__(self):
        self.terms = {}
        self.term_map = {}

    def add_term(self, term, offset, length, file_name, term_id):
        if term not in self.terms:
            self.terms[term] = {}
            self.term_map[term] = term_id
        self.terms[term][file_name] = CatalogTerm(term, offset, length)

    def remove_term(self, term):
        del self.terms[term]
        del self.term_map[term]


# Store term, offset, and length
class CatalogTerm:
    def __init__(self, term, offset, length):
        self.term = term
        self.offset = offset
        self.length = length


# Read stoplist
def get_stopwords():
    with open("stoplist.txt") as f:
        stop_words = f.readlines()
    return set(map(str.strip, stop_words))


# Get documents from file
def get_docs(file):
    f = file.read()
    page = "<root>" + f + "</root>"
    soup = BeautifulSoup(page, features='xml')
    return soup.find_all('DOC')


# Get text of document
def get_text(document):
    text = ""
    all_texts = document.find_all('TEXT')
    for t in all_texts:
        text += t.get_text().strip() + ""
    return clean(text)


# Clean text of unneeded characters
def clean(text):
    text = regex.sub("[^\P{P}\-.,%]+", "", text)
    text = text.replace("`", " ")
    text = text.replace("-", " ")
    text = text.replace(",", " ")
    text = re.sub('\.\.+', ' ', text)
    return text


# Get length of document
def get_document_length(document):
    count = 0
    for line in document.splitlines():
        word = re.sub('\s+', ' ', line).strip().split(' ')
        count += len(word)
    return count


# Stem text to get root of words
def stem_text(text):
    stem_text = ""
    for word in text.split():
        if word.endswith("."):
            stem_text += stemmer.stem(word[:len(word) - 1].lower()) + " "
        else:
            stem_text += stemmer.stem(word.lower()) + " "
    return stem_text


# Get tokens from text
def tokenize(text):
    token_list = []
    i = 0
    tokens = re.split("[^\w\.]*", text)
    for token in tokens:
        token = re.sub(r'\.(?=\s)', '', token)
        if token.__contains__('.'):
            chars = token.split('.')
            for c in chars:
                if not c.isdigit():
                    if len(c) > 1:
                        token = re.sub('\.', ' ', token)
                        break
                else:
                    break
        token = token.lower()
        if token != '':
            i += 1
            token_list.append([token, i])
    return token_list


# Construct dictionary of terms that contain Terms- hold term frequency and position
def construct_offset_dict(given_tokens):
    offset_dict = defaultdict(lambda: defaultdict(Term))
    stopwords = get_stopwords()
    for token in given_tokens:
        doc_id = token[2]
        if token[0] not in stopwords:
            if token[0] in offset_dict:
                if doc_id in offset_dict[token[0]]:
                    offset_dict[token[0]][doc_id].tf = offset_dict[token[0]][doc_id].get_term_frequency() + 1
                    offset_dict[token[0]][doc_id].position.append(token[1])
                else:
                    offset_dict[token[0]][doc_id] = Term(1, [token[1]])
            else:
                doc_dict = defaultdict(Term)
                doc_dict[doc_id] = Term(1, [token[1]])
                offset_dict[token[0]] = doc_dict
    return offset_dict


# Find total term frequency and document frequency
def find_ttf_and_df(offset_dict, term):
    ttf = 0
    df = 0
    for doc_id in offset_dict[term]:
        df += 1
        ttf += offset_dict[term][doc_id].get_term_frequency()
    return ttf, df


# Load inverted index into catalog to store term, offset, and length
def load_catalog(offset_dict, file_name, inv_file_num, catalog_file = None):
    f = '%s%s.txt' %(file_name, inv_file_num)
    inv_file = open(f, "a+")
    for term in offset_dict:
        # Sort dict by term frequency- most frequent are first.  Specified by instructions to facilitate merging.
        offset_dict[term] = OrderedDict(sorted(offset_dict[term].items(), key=lambda x: x[1].tf, reverse=True))
        offset = inv_file.tell()
        ttf, df = find_ttf_and_df(offset_dict, term)
        if catalog_file != None:
            term_id = catalog.term_map[term]
            catalog.remove_term(term)
        else:
            if term not in catalog.term_map:
                term_id = len(catalog.term_map) + 1
            else:
                term_id = catalog.term_map[term]
        input_str = [str(term_id)]
        input_str.append(',')
        input_str.append(str(df))
        input_str.append(',')
        input_str.append(str(ttf))
        input_str.append(':')
        for doc in offset_dict[term]:
            if catalog_file != None:
                doc_id = doc
            else:
                if doc not in doc_num_set:
                    doc_id = len(doc_map) + 1
                    doc_num_set[doc] = doc_id
                    doc_map[doc_id] = doc
                else:
                    doc_id = doc_num_set[doc]
            input_str.append(str(doc_id))
            input_str.append(',')
            input_str.append(str(offset_dict[term][doc].get_term_frequency()))
            input_str.append(',')
            input_str.append(','.join(str(e) for e in offset_dict[term][doc].get_position()))
            input_str.append(';')
        input_str[len(input_str) - 1] = '\n'
        write_str = ''.join(input_str)
        length = len(write_str)
        catalog.add_term(term, offset, length, f, term_id)

        if catalog_file != None:
            catalog_file.write(str(term_id) + ',' + str(offset) + ',' + str(length) + '\n')
        else:
            temp_cat_file = open('Files/Stemmed/catalog_file%d.txt' % (inv_file_num), 'a+')
            temp_cat_file.write(str(term_id) + ',' + str(offset) + ',' + str(length) + '\n')
            temp_cat_file.close()

        inv_file.write(write_str)
    inv_file.close()
    return inv_file_num + 1


def create_index(tokens, flag, inv_file):
    # Make dictionary of terms- offsets dictionary
    offset_dict = construct_offset_dict(tokens)
    # Create inverted file
    inv_file = load_catalog(offset_dict, "Files/Stemmed/inverted_file", inv_file)
    return inv_file


def get_tokens():
    path = "/Users/celiasherry/Documents/NE/Spring2020/IR/HW/HW2/Assignment2/AP_DATA/ap89_collection/"
    #filename = "ap890101"

    num_docs = 0
    length_dict = {}
    tokens = []
    flag = 1
    inv_file = 1

    for filename in os.listdir(path):
        f = open(path + filename)
        documents = get_docs(f)
        for document in documents:
            num_docs += 1
            # Get text of document
            text = get_text(document)
            # Get document ID
            doc_id = document.find('DOCNO').get_text().strip()
            # Get length of document- stop words are included
            doc_length = get_document_length(text)
            # Store length of document in dictionary
            length_dict[doc_id] = doc_length
            # Stem text to get word roots
            stemmed_text = stem_text(text)
            # Tokenize stemmed text
            token_positions = tokenize(stemmed_text)

            # Add document id to each token so it is (term, position, document_id)
            for token in token_positions:
                token.append(doc_id)
            # Add position tokens to list of all tokens
            tokens += token_positions

            if num_docs == 1000:
                num_docs = 0
                inv_file = create_index(tokens, flag, inv_file)
                tokens = []
                flag = 0

    if num_docs < 1000:
        inv_file = create_index(tokens, flag, inv_file)

    pickler('Files/Stemmed/Pickles/termMap.p', catalog.term_map)
    write_hash_map(catalog.term_map, 'term_map.txt')

    pickler('Files/Stemmed/Pickles/docMap.p', doc_map)
    write_hash_map(doc_map, 'docMap.txt')

    pickler('Files/Stemmed/Pickles/lengthMap.p', length_dict)


def write_hash_map(map, f_name):
    map_file = open('Files/Stemmed/Maps/%s' % (f_name), 'a+')
    for key, value in map.items():
        map_file.write(str(key) + ',' + str(value) + '\n')
    map_file.close()


def pickler(path, ds):
    f = open(path, 'wb')
    dill.dump(ds, f)
    f.close()


def load_inverted_list(offset, length, inverted_file):
    inverted_file.seek(offset)
    s = inverted_file.read(length)
    doc_dict = OrderedDict()
    rem_str = s.split(':')[1].split(';')
    for item in rem_str:
        doc_id = item.split(',')[0]
        tf = int(item.split(',')[1])
        position = [int(e) for e in item.split(',')[2:len(item.split(','))]]
        doc_dict[doc_id] = Term(tf, position)
    return doc_dict


def merge_inverted_index_files():
    term_dict = OrderedDict()
    inverted_list = OrderedDict
    catalog_file = open('Files/Stemmed/catalog_file.txt', 'a+')
    for term in catalog.terms:
        for file in catalog.terms[term]:
            inverted_file = open(file)
            inverted_list[term] = load_inverted_list(catalog.terms[term][file].offset, catalog.terms[term][file].length,
                                               inverted_file)
            inverted_file.close()
            if term not in term_dict:
                term_dict[term] = inverted_list[term]
            else:
                for doc_id in inverted_list[term]:
                    if doc_id in term_dict[term]:
                        term_dict[term][doc_id].tf = term_dict[term][doc_id].get_term_frequency() + 1
                        term_dict[term][doc_id].position.extend(inverted_list[term][doc_id].position)
                    else:
                        term_dict[term][doc_id] = Term(inverted_list[term][doc_id].tf,
                                                       inverted_list[term][doc_id].position)
        term_dict[term] = OrderedDict(sorted(term_dict[term].items(), key=lambda x: x[1].tf, reverse=True))
        if len(term_dict) == 1000:
            load_catalog(term_dict, "Files/Stemmed/inverted_file", 0, catalog_file)
            term_dict = {}
    if len(term_dict) > 0:
        load_catalog(term_dict, "Files/Stemmed/inverted_file", 0, catalog_file)
    catalog_file.close()


# Initialize stemmer
stemmer = PorterStemmer()
doc_map = {}
catalog = Catalog()
doc_num_set = {}


def main():
    get_tokens()
    merge_inverted_index_files()

main()