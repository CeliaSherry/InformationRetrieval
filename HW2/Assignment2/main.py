from bs4 import BeautifulSoup
import regex
import re
from nltk.stem import PorterStemmer
from collections import defaultdict

# Store term frequency and term position
class Term:
    def __init__(self, tf, position):
        self.tf = tf
        self.position = position

    def get_term_frequency(self):
        return self.tf

    def get_position(self):
        return self.position

stemmer = PorterStemmer()

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


def load_catalog(offset_dict, file_name, inv_file_num, catalog_file = None):
    f = '%s%s.txt' %(file_name, inv_file_num)



def create_index(tokens, flag, inv_file):
    # Make dictionary of terms- offsets dictionary
    offset_dict = construct_offset_dict(tokens)
    # Create inverted file
    inv_file = load_catalog(offset_dict, "inverted_file", inv_file)
    return inv_file


def get_tokens():
    path = "/Users/celiasherry/Documents/NE/Spring2020/IR/HW/HW2/Assignment2/AP_DATA/ap89_collection/"
    filename = "ap890101"

    num_docs = 0
    num_files = 0
    length_dict = {}
    tokens = []
    flag = 1
    inv_file = 1

    #for filename in os.listdir(path):
       # num_files += 1

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



#print(get_document_length(get_text(get_tokens()[0])))
#print(tokenize("this is a test. movies 1895 10.20 1,000 this"))
#print(get_tokens())
tokens = get_tokens()
print(tokens)
#d = construct_offset_dict(tokens)
#print(d['people'])