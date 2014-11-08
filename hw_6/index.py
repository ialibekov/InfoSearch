#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from struct import pack, unpack
from pymystem3 import Mystem
import random
import pickle


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
        i = n -1
        for i in reversed(range(n)):
            number = ((values & (2**(28/n)-1 << 28 / n * i)) >> 28 / n * i) + 1
            numbers.append(number)
    return numbers


def pack_doc_ids(doc_ids):
    doc_ids_diff = doc_ids[:1] + [j-i for i, j in zip(doc_ids[:-1], doc_ids[1:])]
    return s9_encode(doc_ids_diff)


def unpack_doc_ids(packed_doc_ids):
    doc_ids = s9_decode(packed_doc_ids)
    # replacing the difference between docIds with docIds
    x = 0
    for i in xrange(len(doc_ids)):
        t = doc_ids[i]
        doc_ids[i] += x
        x += t
    return doc_ids


class Index(object):
    def __init__(self, input_file):
        self.stemmer = Mystem()
        self.tokens = list()
        self.index = dict()
        self.number_of_documents = 0

        try:
            self.read_from_file_compressed("index_compressed.txt")
        except:
            # reading documents, making tokenization
            with open(input_file, "r") as f:
                for line in f:
                    self.number_of_documents += 1
                    # self.documents[i] = line.decode("utf-8")
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
                    self.index[current_term] = (len(doc_ids), pack_doc_ids(doc_ids))
                    current_term = term
                    current_doc_id = doc_id
                    doc_ids = [doc_id]
            self.index[current_term] = (len(doc_ids), pack_doc_ids(doc_ids))
            del self.tokens
            self.write_index_in_file()

    def write_index_in_file(self):
        with open("index_compressed.txt", "w") as f:
            pickle.dump(self.index, f)

    def read_from_file_compressed(self, index_file):
        with open(index_file, "r") as f:
            self.index = pickle.load(f)


def test():
    print "VarByte test"
    random_list = random.sample(xrange(1, 1000), random.randrange(1, 8))
    print "Random list: {}".format(random_list)
    c = vb_encode(random_list)
    print "Encrypted: {}".format(repr(c))
    print "Decrypted: {}".format(vb_decode(c))

    print "\n\n--------------------\n\n"

    print "Simple9 test"
    random_list = random.sample(xrange(1, 1000), random.randrange(1, 8))
    print "Random list: {}".format(random_list)
    c = s9_encode(random_list)
    print "Encrypted: {}".format(repr(c))
    print "Decrypted: {}".format(s9_decode(c))


def main():
    print "Index is building. Wait for a minute..."
    Index("input_text.txt")
    print "Finished building index.\n\n"
    test()


if __name__ == "__main__":
    main()