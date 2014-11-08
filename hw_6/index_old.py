#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from pymystem3 import Mystem
import pickle


class Index(object):

    def __init__(self, input_file):
        self.stemmer = Mystem()
        self.tokens = list()
        self.index = dict()
        self.number_of_documents = 0

        try:
            self.read_from_file_compressed("index_raw.txt")
        except:
            # reading documents, making tokenization
            with open(input_file, "r") as f:
                for line in f:
                    self.number_of_documents += 1
                    for word in self.stemmer.lemmatize(line):
                        token = word.translate(None, '.,?!:;()"\'-').decode("utf-8").strip()
                        if token:
                            self.tokens.append((token, self.number_of_documents))

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
                    self.index[current_term] = (len(doc_ids), doc_ids)
                    current_term = term
                    current_doc_id = doc_id
                    doc_ids = [doc_id]
            self.index[current_term] = (len(doc_ids), doc_ids)
            del self.tokens
            self.write_index_to_file()

    def write_index_to_file(self):
        with open("index_raw.txt", "w") as f:
            pickle.dump(self.index, f)

    def read_from_file_compressed(self, index_file):
        with open(index_file, "r") as f:
            self.index = pickle.load(f)


def main():
    print "Index is building. Wait for a minute..."
    Index("input_text.txt")
    print "Finished building index.\n\n"


if __name__ == "__main__":
    main()
