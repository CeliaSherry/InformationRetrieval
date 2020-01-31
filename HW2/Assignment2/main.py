from bs4 import BeautifulSoup
import regex
import re
import os
from nltk.stem import PorterStemmer

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

def create_index(tokens, flag, inv_file):
    doc_id = tokens[0][2]


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
    if num_docs < 1000
        inv_file = create_index(tokens, flag, inv_file)



#print(get_document_length(get_text(get_tokens()[0])))
print(tokenize("this is a test. movies 1895 10.20 1,000 this"))