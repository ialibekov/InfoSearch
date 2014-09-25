#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from pymystem3 import Mystem


class Index(object):

    def __init__(self, input_file):
        self.stemmer = Mystem()
        self.documents = dict()
        self.tokens = list()
        self.terms = dict()
        self.index = list()

        # reading documents, making tokenization
        with open(input_file, "r") as f:
            for i, line in enumerate(f, start=1):
                self.documents[i] = line.decode("utf-8")
                for word in self.stemmer.lemmatize(line):
                    token = word.translate(None, '.,?!:;()"\'-').decode("utf-8").strip()
                    if token:
                        self.tokens.append((token, i))

        # sorting by tokens first, then by frequency
        self.tokens.sort(key=lambda tup: (tup[0], tup[1]))

        # terminization and building index
        current_term = self.tokens[0][0]
        current_doc_id = self.tokens[0][1]
        doc_ids = [current_doc_id]
        for token, doc_id in self.tokens:
            term = token.lower()
            if term == current_term:
                if doc_id != current_doc_id:
                    doc_ids.append(doc_id)
                    current_doc_id = doc_id
            else:
                self.terms[current_term] = (len(doc_ids), doc_ids)
                self.index.append((current_term, len(doc_ids), doc_ids))
                current_term = term
                current_doc_id = doc_id
                doc_ids = [doc_id]
        self.terms[current_term] = (len(doc_ids), doc_ids)
        self.index.append((current_term, len(doc_ids), doc_ids))

    def print_to_file(self):
        with open("result.txt", "w") as f:
            for term, count, doc_ids in self.index:
                f.write("{},\t{},\t{}\n".format(term.encode("utf-8"), count, doc_ids))

    def print_statistics(self):
        terms_num = len(self.terms)
        terms_len = 0.
        for term in self.terms:
            terms_len += len(term)

        print "***********************"
        print "Number of terms = {}".format(terms_num)
        print "Average term length = {}".format(terms_len / terms_num)
        print "***********************"


def main():
    index = Index("input_text.txt")
    index.print_to_file()
    index.print_statistics()

if __name__ == "__main__":
    main()
