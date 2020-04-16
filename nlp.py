import re
import math

import nltk
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from tabulate import tabulate
from operator import itemgetter

STOPWORDS = set(stopwords.words("english"))

SORT_ALPHA = "alpha"
SORT_OCCURRENCES = "occurrences"
SORT_LENGTH = "length"

DEFAULT_STOPWORDS = False
DEFAULT_SORT = SORT_OCCURRENCES


def common(model, answer):
    texts = [t.lower() for t in [model, answer]]
    tokens = [nltk.word_tokenize(t) for t in texts]

    tokens = [[word for word in t if word.isalpha()] for t in tokens]

    fdists = [FreqDist(t) for t in tokens]

    tokens = [set(t) for t in tokens]

    total = set.union(*tokens)
    total -= STOPWORDS

    matches = {word for word in set.intersection(*tokens)}

    matches -= STOPWORDS

    matches = [
        (word, min([f.get(word) for f in fdists]), len(word)) for word in matches
    ]

    return len(matches)/len(total)


class Ngrams(object):
    ngram_joiner = " "

    def __init__(self, text, n=3):
        self.n = n
        self.text = text
        self.d = self.text_to_ngrams(self.text, self.n)

    def __getitem__(self, word):
        return self.d[word]

    def __contains__(self, word):
        return word in self.d

    def __iter__(self):
        return iter(self.d)

    def __mul__(self, other):
        if self.n != other.n:
            raise self.WrongN
        if self.text == other.text:
            return 1.0
        return sum(self[k]*other[k] for k in self if k in other)

    def __repr__(self):
        return "Ngrams(%r, %r)" % (self.text, self.n)

    def __str__(self):
        return self.text

    def tokenize(self, text):
        return re.compile(u'[^\w\n ]|\xe2', re.UNICODE).sub('', text).lower().split()

    def normalize(self, text):
        try:
            return text.lower()
        except AttributeError:
            raise TypeError(text)

    def make_ngrams(self, text):
        text = self.normalize(text)
        tokens = self.tokenize(text)
        return (self.ngram_joiner.join(tokens[i:i+self.n]) for i in range(len(tokens)))

    def text_to_ngrams(self, text, n=3):
        d = {}
        for ngram in self.make_ngrams(text):
            try:
                d[ngram] += 1
            except KeyError:
                d[ngram] = 1

        norm = math.sqrt(sum(x**2 for x in d.values()))
        for k, v in d.items():
            d[k] = v/norm
        return d
