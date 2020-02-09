from bs4 import BeautifulSoup
import regex
import re
import os
from nltk.stem import PorterStemmer
from collections import defaultdict
from collections import OrderedDict
import dill
import pickle
import zlib
import gzip


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

    def get_term(self):
        return self.term


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
def load_catalog(term_dict, file_name, inv_file_num, catalog_file=None, demo=0):
    f = '%s%s.txt' %(file_name, inv_file_num)
    #inv_file = gzip.open(f, "wt+")
    #if inv_file_num == 0:
        #inv_file = open(f, "wb+")
    #else:
    inv_file = open(f, "a+")
    for term in term_dict:
        # Sort dict by term frequency- most frequent are first.  Specified by instructions to facilitate merging.
        term_dict[term] = OrderedDict(sorted(term_dict[term].items(), key=lambda x: x[1].tf, reverse=True))
        offset = inv_file.tell()
        ttf, df = find_ttf_and_df(term_dict, term)
        if demo == 1:
            term_id = term
        elif catalog_file is not None:
            term_id = catalog.term_map[term]
            #catalog.remove_term(term)
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
        for doc in term_dict[term]:
            if catalog_file is not None:
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
            input_str.append(str(term_dict[term][doc].get_term_frequency()))
            input_str.append(',')
            input_str.append(','.join(str(e) for e in term_dict[term][doc].get_position()))
            input_str.append(';')
        input_str[len(input_str) - 1] = '\n'
        write_str = ''.join(input_str)
        length = len(write_str)
        catalog.add_term(term, offset, length, f, term_id)

        if catalog_file is not None:
            #byte_length = len(zlib.compress(write_str.encode()))
            catalog_file.write(str(term_id) + ',' + str(offset) + ',' + str(length) + '\n')
        else:
            temp_cat_file = open('Files/Demo/catalog_file%d.txt' % (inv_file_num), 'a+')
            temp_cat_file.write(str(term_id) + ',' + str(offset) + ',' + str(length) + '\n')
            temp_cat_file.close()

        #if inv_file_num == 0:
            #a = zlib.compress(write_str.encode())
            #inv_file.write(a)
            #test = open("Files/Demo/test", "a+")
            #test.write(write_str)
        #else:
        inv_file.write(write_str)
    inv_file.close()
    return inv_file_num + 1


def create_index(tokens, flag, inv_file):
    # Make dictionary of terms- offsets dictionary
    offset_dict = construct_offset_dict(tokens)
    # Create inverted file
    #inv_file = load_catalog(offset_dict, "Files/Stemmed/inverted_file", inv_file)
    inv_file = load_catalog(offset_dict, "Files/Demo/inverted_file", inv_file)
    return inv_file


def get_tokens():
    path = "/Users/celiasherry/Documents/NE/Spring2020/IR/HW/HW2/Assignment2/AP_DATA/ap89_collection/"
    #filename = "ap890101"

    num_docs = 0
    length_dict = {}
    tokens = []
    flag = 1
    inv_file = 1
    file_no = 0
    file_total = len(os.listdir(path))-1

    for filename in os.listdir(path):
        file_no +=1
        print('Indexing ' + str(file_no) + ' out of ' + str(file_total))
        f = open(path + filename, encoding='ISO-8859-1')
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

    #pickler('Files/Stemmed/Pickles/termMap.p', catalog.term_map)
    pickler('Files/Demo/Pickles/termMap.p', catalog.term_map)
    write_hash_map(catalog.term_map, 'term_map.txt')

    #pickler('Files/Stemmed/Pickles/docMap.p', doc_map)
    pickler('Files/Demo/Pickles/docMap.p', doc_map)
    write_hash_map(doc_map, 'docMap.txt')

    #pickler('Files/Stemmed/Pickles/lengthMap.p', length_dict)
    pickler('Files/Demo/Pickles/lengthMap.p', length_dict)

    #pickler('Files/Stemmed/Pickles/catalog.p', catalog.terms)
    pickler('Files/Demo/Pickles/catalog.p', catalog.terms)


def write_hash_map(map, f_name):
    #map_file = open('Files/Stemmed/Maps/%s' % (f_name), 'a+')
    map_file = open('Files/Demo/Maps/%s' % (f_name), 'a+')
    for key, value in map.items():
        map_file.write(str(key) + ',' + str(value) + '\n')
    map_file.close()


def pickler(path, ds):
    f = open(path, 'wb')
    dill.dump(ds, f)
    f.close()


def unpickler(file):
    f = open(file, 'rb')
    ds = dill.load(f)
    f.close()
    return ds


def load_inverted_list(offset, length, inverted_file, term, doc_map=None):
    inverted_list = OrderedDict()
    inverted_file.seek(offset)
    s = inverted_file.read(length)
    doc_dict = OrderedDict()
    rem_str = s.split(':')[1].split(';')
    for item in rem_str:
        doc_no = item.split(',')[0]
        if doc_map is not None:
            doc_id = doc_map.get(int(doc_no))
        else:
            doc_id = doc_no
        tf = int(item.split(',')[1])
        position = [int(e) for e in item.split(',')[2:len(item.split(','))]]
        doc_dict[doc_id] = Term(tf, position)
    inverted_list[term] = doc_dict
    return inverted_list


def merge_inverted_index_files():
    term_dict = OrderedDict()
    #catalog_file = open('Files/Stemmed/catalog_file.txt', 'a+')
    catalog_file = open('Files/Demo/catalog_file.txt', 'a+')
    #catalog_terms = unpickler('Files/Stemmed/Pickles/catalog.p')
    catalog_terms = unpickler('Files/Demo/Pickles/catalog.p')
    for term in catalog_terms:
        for file in catalog_terms[term]:
            inverted_file = open(file)
            inverted_list = load_inverted_list(catalog_terms[term][file].offset, catalog_terms[term][file].length,
                                               inverted_file, term)
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
            #load_catalog(term_dict, "Files/Stemmed/inverted_file", 0, catalog_file)
            load_catalog(term_dict, "Files/Demo/inverted_file", 0, catalog_file)
            term_dict = {}
    if len(term_dict) > 0:
        #load_catalog(term_dict, "Files/Stemmed/inverted_file", 0, catalog_file)
        load_catalog(term_dict, "Files/Demo/inverted_file", 0, catalog_file)
    catalog_file.close()


def combine_inverted_index(i1, i2, term):
    inverted_list = OrderedDict()
    doc_dict = {}
    for item in i1[term]:
        doc_dict[item] = i1[term][item]
    for item in i2[term]:
        doc_dict[item] = i2[term][item]
    inverted_list[term] = doc_dict
    return inverted_list



def merge_files(file1, file2, catalog1, catalog2, output_file):
    print('Merging files')
    term_dict = OrderedDict()
    catalog_file = open('Files/Demo/merged_catalog_file.txt', 'a+')

    f1 = open(file1, "r")
    f2 = open(file2, "r")

    cat1 = parse_catalog(catalog1)
    cat2 = parse_catalog(catalog2)

    for term in cat1:
        offset = int(cat1[term][0])
        length = int(cat1[term][1])
        inverted_index = load_inverted_list(offset, length, f1, term)
        if term in cat2:
            offset2 = int(cat2[term][0])
            length2 = int(cat2[term][1])
            inverted_index2 = load_inverted_list(offset2, length2, f2, term)
            inverted_index = combine_inverted_index(inverted_index, inverted_index2, term)
        term_dict[term] = inverted_index[term]
    for term2 in cat2:
        if term2 not in cat1:
            offset = int(cat2[term2][0])
            length = int(cat2[term2][1])
            inverted_index = load_inverted_list(offset, length, f2, term2)
            term_dict[term2] = inverted_index[term2]
    load_catalog(term_dict, output_file, 0, catalog_file,1)


def parse_catalog(file):
    catalog = {}
    catalog_file = open(file, 'r')
    for line in catalog_file.readlines():
        text = line.strip().split(',')
        catalog[text[0]] = text[1:]
    return catalog



# Initialize stemmer
stemmer = PorterStemmer()
doc_map = {}
catalog = Catalog()
doc_num_set = {}


def main():
    get_tokens()
    merge_inverted_index_files()

#main()
#merge_files('Files/Demo/inverted_file1.txt', 'Files/Demo/inverted_file2.txt', 'Files/Demo/catalog_file1.txt', 'Files/Demo/catalog_file2.txt','Files/Demo/merged_invertedfile.txt')