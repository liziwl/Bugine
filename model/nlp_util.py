from nltk.tokenize import RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
# from nltk.stem import PorterStemmer
# Porter2 is Snowball
from string import punctuation
from humps import decamelize as decam
import re
import copy
from model import work_path


def get_stops():
    stops = set(punctuation)
    with open(work_path.in_project("./model/conf/stopwords.dat"), 'r', encoding='utf8') as f:
        for row in f.readlines():
            tmp = row.strip()
            if tmp != "":
                stops.add(tmp)
    return stops


def get_hot_keys():
    hot_k = set()
    with open(work_path.in_project("./model/conf/hotkey.dat"), 'r', encoding='utf8') as f:
        for row in f.readlines():
            tmp = row.strip()
            if tmp != "":
                tmp = stem_word(tmp)
                hot_k.add(tmp)
    return hot_k


def get_concern_label():
    c_label = set()
    with open(work_path.in_project("./model/conf/concern_label.dat"), 'r', encoding='utf8') as f:
        for row in f.readlines():
            tmp = row.strip()
            if tmp != "":
                c_label.add(tmp)
    return c_label


def tokenize(corpus):
    ret = RegexpTokenizer('[a-zA-Z0-9\'\'.]+')
    corpus_tokens = [ret.tokenize(i.lower()) for i in corpus]
    return corpus_tokens


def remove_stop(corpus):
    stops = get_stops()
    filtered_corpus = [[w for w in t if not w in stops] for t in corpus]
    return filtered_corpus


def stemming(corpus):
    ess = SnowballStemmer('english', ignore_stopwords=True)
    stemmed_corpus = [[ess.stem(w) for w in t] for t in corpus]
    return stemmed_corpus


def stem_word(word):
    corpus = [[word, ], ]
    return stemming(corpus)[0][0]


def stem_sentence(a_sentence):
    out = stem_corpus([a_sentence, ])
    return out[0]


def stem_corpus(corpus, remove_stopwords=True):
    tmp_corpus = copy.deepcopy(corpus)
    tmp_corpus = tokenize(tmp_corpus)
    if remove_stopwords:
        tmp_corpus = remove_stop(tmp_corpus)
    tmp_corpus = stemming(tmp_corpus)
    return tmp_corpus


def word_count(text):
    build_corpus = [text, ]
    tmp = tokenize(build_corpus)[0]
    return len(tmp)


def decamelize(w, mode=1):
    if mode == 1:
        return decam(w)
    elif mode == 2:
        return "_".join(re.findall('[A-Z][^A-Z]*', w))


def split_under(w):
    return re.split('_+', w)


def combine_process(w):
    tmp = decamelize(w)
    tmp = split_under(tmp)
    return tmp


def split_dot(w):
    tmp = w.split(".")[-1]
    tmp = combine_process(tmp)
    return tmp


def process_xsv(xsv_output):
    output = copy.deepcopy(xsv_output)
    for i in range(len(output)):
        output[i][0] = combine_process(output[i][0])
        output[i][1] = split_dot(output[i][1])
        output[i][2] = combine_process(output[i][2])

    return output


def split_label(label_list):
    out = []
    for i in range(len(label_list)):
        tmp = list(filter(lambda item: item != "", label_list[i].split("#")))
        tmp = " ".join(tmp)
        tmp = tmp.lower()
        out.append(tmp)
    return out


# nlp = spacy.load('en_core_web_sm', disable=['ner', 'parser'])

# def lema(word):
#     doc = nlp(word)
#     return " ".join([token.lemma_ for token in doc])
#
#
# def lema_for_list(same_list):
#     ps = PorterStemmer()
#     same_list2 = copy.deepcopy(same_list)
#     for i in range(len(same_list2)):
#         for j in range(len(same_list2[i])):
#             same_list2[i][j] = ps.stem((lema(same_list2[i][j])).lower())
#     return same_list2

if __name__ == "__main__":
    print(stemming(remove_stop(tokenize(["I'm working on jobs"]))))
    print(stem_word("working"))
    print(stem_sentence("I'm working on jobs"))
    print(word_count("I'm working on jobs"))
    print(decamelize("AfvsdfgbBsdfafv"))
