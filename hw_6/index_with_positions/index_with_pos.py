#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from struct import pack, unpack
from pymystem3 import Mystem


def vb_encode_number(number):
    bytes = list()
    while True:
        bytes.insert(0, number % 128)
        if number < 128:
            break
        number /= 128
    bytes[-1] += 0x80
    return pack('{0}B'.format(len(bytes)), *bytes)


def vb_encode(numbers):
    bytes = list()
    for number in numbers:
        bytes.append(vb_encode_number(number))
    return ''.join(bytes)


def vb_decode(bytestream):
    n = 0
    numbers = list()
    bytestream = unpack('{0}B'.format(len(bytestream)), bytestream)
    for byte in bytestream:
        if byte < 128:
            n = 128 * n + byte
        else:
            n = 128 * n + (byte - 128)
            numbers.append(n)
            n = 0
    return numbers


NUM_OF_INT_IN_DW = [1, 2, 3, 4, 5, 7, 9, 14, 28]


def s9_encode(numbers):
    res = ""
    while len(numbers):
        for n in reversed(NUM_OF_INT_IN_DW):
            if len(numbers) >= n:
                if all(i.bit_length() <= 28 / n for i in numbers[:n]):
                    tmp = NUM_OF_INT_IN_DW.index(n) << 28
                    i = n - 1
                    for elem in numbers[:n]:
                        tmp += elem - 1 << 28 / n * i
                        i -= 1
                    res += pack('=i', tmp)
                    numbers = numbers[n:]
                    break
    return res


def s9_decode(bytestream):
    numbers = list()
    intstream = unpack('{0}i'.format(len(bytestream) / 4), bytestream)
    for integer in intstream:
        info = (integer & 0xf0000000) >> 28
        values = integer & 0x0fffffff
        n = NUM_OF_INT_IN_DW[info]
        for i in reversed(range(n)):
            number = ((values & (2 ** (28 / n) - 1 << 28 / n * i)) >> 28 / n * i) + 1
            numbers.append(number)
    return numbers


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
                pos = 1
                self.documents[i] = line.decode("utf-8")
                for word in self.stemmer.lemmatize(line):
                    token = word.translate(None, '.,?!:;()"\'-').decode("utf-8").strip()
                    if token:
                        self.tokens.append((token, i, pos))
                        pos += 1

        # sorting by tokens first, then by frequency
        self.tokens.sort(key=lambda tup: (tup[0], tup[1]))

        # terminization and building index
        current_term = self.tokens[0][0]
        current_doc_id = self.tokens[0][1]
        pos = self.tokens[0][1]
        doc_ids = [current_doc_id]
        positions_in_docs = list()
        positions = [pos]
        for token, doc_id, pos in self.tokens:
            term = token.lower()
            if term == current_term:
                if doc_id != current_doc_id:
                    doc_ids.append(doc_id)
                    current_doc_id = doc_id
                    positions_in_docs.append(positions)
                    positions = [pos]
                else:
                    positions.append(pos)
            else:
                positions_in_docs.append(positions)
                self.terms[current_term] = (len(doc_ids), doc_ids)
                self.index.append((current_term, len(doc_ids), doc_ids, positions_in_docs))
                current_term = term
                current_doc_id = doc_id
                doc_ids = [doc_id]
                positions_in_docs = list()
                positions = [pos]
        self.terms[current_term] = (len(doc_ids), doc_ids)
        self.index.append((current_term, len(doc_ids), doc_ids, positions_in_docs))

    def print_to_file(self):
        with open("result.txt", "w") as f:
            for term, count, doc_ids, positions_in_docs in self.index:
                f.write("{},\t{},\t{},\t{}\n".format(term.encode("utf-8"), count, doc_ids,
                                                     "{}".format(positions_in_docs)))

    def print_to_file_compressed(self):
        with open("result_compressed.txt", "w") as f:
            for term, count, doc_ids, positions_in_docs in self.index:
                # replacing docIds with difference between them
                doc_ids = doc_ids[:1] + [j - i for i, j in zip(doc_ids[:-1], doc_ids[1:])]
                encoded_positions = list()
                for positions in positions_in_docs:
                    encoded_positions.append(vb_encode(positions[:1] + [j - i for i, j in zip(positions[:-1],
                                                                                              positions[1:])]))
                f.write("{},\t{},\t{},\t{}\n".format(term.encode("utf-8"), count, s9_encode(doc_ids),
                                                     "{}".format(encoded_positions)))

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
    print "Index is building. Wait for a minute..."
    index = Index("input_text.txt")
    print "Finished building index.\n\n"
    index.print_to_file()
    index.print_to_file_compressed()
    # index.print_statistics()


if __name__ == "__main__":
    main()
