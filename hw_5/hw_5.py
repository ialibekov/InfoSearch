#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from math import log10
from pymystem3 import Mystem


def is_cyrillic(s):
    return not all(ord(c) < 300 for c in s)


class Runner(object):
    def __init__(self, input_text):
        self.lemmatize = None
        while True:
            response = raw_input("Do you want to lemmatize text first? (yes/no)\n").lower()
            if response == "yes":
                print "You should wait for a while"
                self.lemmatize = True
                self.stemmer = Mystem()
                break
            elif response == "no":
                self.lemmatize = False
                break

        self.word_lists = list()
        with open(input_text, "r") as f:
            for line in f:
                line += "."
                if self.lemmatize:
                    lexemes = self.stemmer.lemmatize(line)
                    word_list = list()  # список слов, неразделенных знаками пунктуации
                    for lexeme in lexemes:
                        lexeme = lexeme.strip()
                        if lexeme:
                            if lexeme.translate(None, '.,?!:;()"\' -\t\n'):  # проверка, что лексема не является знаком пунктуации
                                lexeme = lexeme.decode("utf-8")
                                if is_cyrillic(lexeme):
                                    word_list.append(lexeme)
                            else:  # иначе, добавить биграмы из списка и завести новый пустой список
                                self.word_lists.append(word_list)
                                word_list = list()
                else:
                    line = line.replace(".", " . ").replace(",", " , ").replace(":", " : ").replace(";", " ; ")\
                        .replace("?", " ? ").replace("!", " ! ").replace("(", " ( ").replace(")", " ) ")\
                        .replace("--", " -- ").replace(".", " . ")
                    word_list = list()
                    for lexeme in line.split():
                        # проверка, что лексема не является знаком пунктуации
                        lexeme = lexeme.translate(None, '.,?!:;()"\'').replace("--", "").decode("utf-8").strip().lower()
                        if lexeme:
                            if is_cyrillic(lexeme):
                                word_list.append(lexeme)
                        else:
                            if word_list:
                                self.word_lists.append(word_list)
                            word_list = list()

        train, test = self.split()
        self.lid = Lid(train, test)
        self.lid.run()

    def split(self):
        n = len(self.word_lists)
        train = self.word_lists[:n*9/10]
        test = self.word_lists[n*9/10:]
        return train, test


class Lid(object):
    def __init__(self, train, test):
        self.train = train
        self.test = test
        self.words_frequency = dict()
        self.bigrams_frequency = dict()
        self.trigrams_frequency = dict()
        self.number_of_words = 0
        self.number_of_bigrams = 0
        self.number_of_trigrams = 0

        for i, words_list in enumerate(self.train):
            n = len(words_list)
            if n > 1:
                w1 = words_list[0]
                w2 = words_list[1]
                self.__add_word(w1)
                self.__add_word(w2)
                self.__add_bigram(w1, w2)
                for w3 in words_list[2:]:  # если n=2, то цикл просто не сработает
                    self.__add_word(w3)
                    self.__add_bigram(w2, w3)
                    self.__add_trigram(w1, w2, w3)
                    w1 = w2
                    w2 = w3
            elif n == 1:
                w1 = words_list[0]
                self.__add_word(w1)
            if i % 5000 == 0:
                print "Training on {} sample in training set".format(i)
        self.v = len(self.words_frequency)
        """
        print "total words     = {:7}".format(self.number_of_words)
        print "unique words    = {:7}".format(self.v)
        print "total bigrams   = {:7}".format(self.number_of_bigrams)
        print "unique bigrams  = {:7}".format(len(self.bigrams_frequency))
        print "total trigrams  = {:7}".format(self.number_of_trigrams)
        print "unique trigrams = {:7}".format(len(self.trigrams_frequency))
        """

    def __add_word(self, word):
        if word in self.words_frequency:
            self.words_frequency[word] += 1
        else:
            self.words_frequency[word] = 1
        self.number_of_words += 1

    def __add_bigram(self, w1, w2):
        bigram = self.__make_n_gram(w1, w2)
        if bigram in self.bigrams_frequency:
            self.bigrams_frequency[bigram] += 1
        else:
            self.bigrams_frequency[bigram] = 1
        self.number_of_bigrams += 1

    def __add_trigram(self, w1, w2, w3):
        trigram = self.__make_n_gram(w1, w2, w3)
        if trigram in self.trigrams_frequency:
            self.trigrams_frequency[trigram] += 1
        else:
            self.trigrams_frequency[trigram] = 1
        self.number_of_trigrams += 1

    def __make_n_gram(self, w1, w2=None, w3=None):
        if w2 is None:
            return w1
        elif w3 is None:
            b = sorted([w1, w2])
            return u"{} {}".format(b[0], b[1])
        else:
            t = sorted([w1, w2, w3])
            return u"{} {} {}".format(t[0], t[1], t[2])

    def __p_lid(self, w1, w2=None, w3=None):
        """
        Возвращает сглаженную условную вероятность по Лидстону, если указано больше одного параметра. Иначе вернет
        сглаженную вероятность слова w1.
        """
        l = 0.5
        if w2 is None:
            return (self.words_frequency.get(w1, 0.0) + l) / (self.number_of_words + l * self.v)
        elif w3 is None:
            b = self.__make_n_gram(w1, w2)
            return (self.bigrams_frequency.get(b, 0.0) + l) / (self.words_frequency.get(w1, 0.0) + l * self.v)
        else:
            b = self.__make_n_gram(w1, w2)
            t = self.__make_n_gram(w1, w2, w3)
            return (self.trigrams_frequency.get(t, 0.0) + l) / (self.bigrams_frequency.get(b, 0.0) + l * self.v ** 2)

    def run(self):
        p = log10(1.0)
        for words_list in self.test:
            n = len(words_list)
            if n > 2:
                w1 = words_list[0]
                w2 = words_list[1]
                w3 = words_list[2]
                p += log10(self.__p_lid(w1) * self.__p_lid(w1, w2) * self.__p_lid(w1, w2, w3))
                w1, w2 = w2, w3
                for w3 in words_list[3:]:
                    p += log10(self.__p_lid(w1, w2, w3))
                    w1, w2 = w2, w3
            elif n == 2:
                w1 = words_list[0]
                w2 = words_list[1]
                p += log10(self.__p_lid(w1) * self.__p_lid(w1, w2))
            elif n == 1:
                w1 = words_list[0]
                p += log10(self.__p_lid(w1))
            if not p:
                break
        print "Lidstone's model probability estimation for training set = 10 ^ {}".format(p)


class Ho(object):
    def __init__(self, train, test):
        n = len(train)
        self.train = (train[:n*9/10], train[n*9/10:])  # training and heldout sets
        self.test = test
        self.words_frequency = [dict(), dict()]
        self.bigrams_frequency = [dict(), dict()]
        self.trigrams_frequency = [dict(), dict()]

        for i, set in enumerate(self.train):
            set_n = i  # 0 - тестовое множество; 1 - heldout множество
            for words_list in set:
                n = len(words_list)
                if n > 1:
                    w1 = words_list[0]
                    w2 = words_list[1]
                    self.__add_word(w1, set_n)
                    self.__add_word(w2, set_n)
                    self.__add_bigram(w1, w2, set_n)
                    for w3 in words_list[2:]:  # если n=2, то цикл просто не сработает
                        self.__add_word(w3, set_n)
                        self.__add_bigram(w2, w3, set_n)
                        self.__add_trigram(w1, w2, w3, set_n)
                        w1 = w2
                        w2 = w3
                elif n == 1:
                    w1 = words_list[0]
                    self.__add_word(w1, set_n)

    def __add_word(self, word, set_n=0):
        if word in self.words_frequency:
            self.words_frequency[set_n][word] += 1
        else:
            self.words_frequency[set_n][word] = 1

    def __add_bigram(self, w1, w2, set_n=0):
        bigram = self.__make_n_gram(w1, w2)
        if bigram in self.bigrams_frequency:
            self.bigrams_frequency[set_n][bigram] += 1
        else:
            self.bigrams_frequency[set_n][bigram] = 1

    def __add_trigram(self, w1, w2, w3, set_n=0):
        trigram = self.__make_n_gram(w1, w2, w3)
        if trigram in self.trigrams_frequency:
            self.trigrams_frequency[set_n][trigram] += 1
        else:
            self.trigrams_frequency[set_n][trigram] = 1

    def __make_n_gram(self, w1, w2=None, w3=None):
        if w2 is None:
            return w1
        elif w3 is None:
            b = sorted([w1, w2])
            return u"{} {}".format(b[0], b[1])
        else:
            t = sorted([w1, w2, w3])
            return u"{} {} {}".format(t[0], t[1], t[2])

    def __p_ho(self, w1, w2, w3):
        pass


def main():
    runner = Runner("corpus.txt")

if __name__ == "__main__":
    main()