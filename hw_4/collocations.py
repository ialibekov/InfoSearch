#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from math import sqrt, log
from pymystem3 import Mystem


def log_l(k, n, x):
    """
    Calculates log(L(k,n,x))
    """
    return k * log(x) + (n - k) * log(1 - x)


def is_cyrillic(s):
    return not all(ord(c) < 300 for c in s)


class CollocationFinder(object):

    def __init__(self, input_text):
        self.number_of_words = 0
        self.number_of_bigrams = 0
        self.words_frequency = dict()
        self.bigrams_frequency = dict()
        self.words_position = dict()  # как часто слово W находится в первой и во второй позиции в биграмме

        while True:
            response = raw_input("Do you want to lemmatize text first? (yes/no)\n").lower()
            if response == "yes":
                print "You should wait for a while"
                LEMMATIZE = True
                stemmer = Mystem()
                break
            elif response == "no":
                LEMMATIZE = False
                break

        with open(input_text, "r") as f:
            for i, line in enumerate(f, start=1):
                line = line + "."
                if LEMMATIZE:
                    lexemes = stemmer.lemmatize(line)
                    words_list = list()  # список слов, неразделенных знаками пунктуации
                    for lexeme in lexemes:
                        lexeme = lexeme.strip()
                        if lexeme:
                            if lexeme.translate(None, '.,?!:;()"\' -\t\n'):  # проверка, что лексема не является знаком пунктуации
                                lexeme = lexeme.decode("utf-8")
                                if is_cyrillic(lexeme):
                                    words_list.append(lexeme)
                            else:  # иначе, добавить биграмы из списка и завести новый пустой список
                                n = len(words_list)
                                if n > 1:
                                    w1 = words_list[0]
                                    self.__add_word(w1)
                                    for w2 in words_list[1:]:
                                        self.__add_word(w2)
                                        self.__add_bigram(w1, w2)
                                        w1 = w2
                                words_list = list()
                else:
                    line = line.replace(".", " . ").replace(",", " , ").replace(":", " : ").replace(";", " ; ")\
                        .replace("?", " ? ").replace("!", " ! ").replace("(", " ( ").replace(")", " ) ")\
                        .replace("--", " -- ").replace(".", " . ")
                    words_list = list()
                    for lexeme in line.split():
                        # проверка, что лексема не является знаком пунктуации
                        lexeme = lexeme.translate(None, '.,?!:;()"\'').replace("--", "").decode("utf-8").strip().lower()
                        if lexeme:
                            if is_cyrillic(lexeme):
                                words_list.append(lexeme)
                        else:
                            n = len(words_list)
                            if n > 1:
                                w1 = words_list[0]
                                self.__add_word(w1)
                                for w2 in words_list[1:]:
                                    self.__add_word(w2)
                                    self.__add_bigram(w1, w2)
                                    w1 = w2
                            words_list = list()

                if i % 1000 == 0:
                    print "Computing line {}".format(i)
            print "total words = {}".format(self.number_of_words)
            print "unique words = {}".format(len(self.words_frequency))
            print "total bigrams = {}".format(self.number_of_bigrams)
            print "unique bigrams = {}".format(len(self.bigrams_frequency))

        with open("bigrams.txt", "w") as f:
            bigrams = list(self.bigrams_frequency.items())
            bigrams.sort(key=lambda tup: (-tup[1], tup[0]))
            for bigram in bigrams:
                f.write("{}\n".format(bigram[0].encode("utf-8")))

    def __add_word(self, word):
        if word in self.words_frequency:
            self.words_frequency[word] += 1
        else:
            self.words_frequency[word] = 1
        self.number_of_words += 1

    def __add_bigram(self, w1, w2):
        bigram = u"{} {}".format(w1, w2)
        if bigram in self.bigrams_frequency:
            self.bigrams_frequency[bigram] += 1
        else:
            self.bigrams_frequency[bigram] = 1
        self.number_of_bigrams += 1
        self.__add_word_position(w1, is_first=True)
        self.__add_word_position(w2, is_first=False)

    def __add_word_position(self, word, is_first=True):
        if word in self.words_position:
            if is_first:
                self.words_position[word][0] += 1
            else:
                self.words_position[word][1] += 1
        else:
            if is_first:
                self.words_position[word] = [1, 0]
            else:
                self.words_position[word] = [0, 1]

    def student_test(self):
        """
        t-критерий Стьюдента. Уровень значимости равен = 0.05. Порог равен 2.576
        """
        threshold = 2.576
        result = list()

        for bigram in self.bigrams_frequency:
            w1, w2 = bigram.split()
            n = self.number_of_words
            m = float(self.words_frequency[w1] * self.words_frequency[w2]) / n ** 2
            x = float(self.bigrams_frequency[bigram]) / n
            t = (x - m) / sqrt((x - x ** 2) / n)
            if t > threshold:
                result.append((bigram, t))
        result.sort(key=lambda tup: tup[1], reverse=True)

        with open("results/student_res.txt", "w") as f:
            for b, t in result:
                f.write("{}\n".format(b.encode("utf-8")))

        i = 0
        length = len(result)
        while (i < 100) and (i < length):
            b, t = result[i]
            print u"{}\t{}".format(t, b)
            i += 1

    def chi_square(self):
        """
        Хи-квадрат критерий. Уровень значимости равен = 0.05. Порог равен 3.841
        """
        threshold = 3.841
        result = list()

        for bigram in self.bigrams_frequency:
            w1, w2 = bigram.split()
            n = self.number_of_words
            o11 = self.bigrams_frequency[bigram]
            o12 = self.words_position[w2][1] - o11
            o21 = self.words_position[w1][0] - o11
            o22 = self.number_of_bigrams - o12 - o21 - o11
            chi = float(n * (o11 * o22 - o12 * o21) ** 2)/((o11 + o12) * (o11 + o21) * (o22 + o12) * (o22 + o21))
            if chi > threshold:
                result.append((bigram, chi))

        result.sort(key=lambda tup: tup[1], reverse=True)

        with open("results/chi_res.txt", "w") as f:
            for b, chi in result:
                f.write("{}\n".format(b.encode("utf-8")))

        i = 0
        length = len(result)
        while (i < 100) and (i < length):
            b, chi = result[i]
            print u"{}\t{}".format(chi, b)
            i += 1

    def likelihood(self):
        """
        Критерий отношения правдоподобия. Значимость = 0.005. Порог = 7.88
        """
        threshold = 7.88
        result = list()
        absolute = list()  # список биграмм, для которых p1 = 1, либо p2 = 0 (для них l = бесконечности)
        # не совсем понял, что с ними делать. Добавил их в топ результата.

        for bigram in self.bigrams_frequency:
            w1, w2 = bigram.split()
            n = self.number_of_words
            c1 = self.words_frequency[w1]
            c2 = self.words_frequency[w2]
            c12 = self.bigrams_frequency[bigram]
            p = float(c2) / n
            p1 = float(c12) / c1
            p2 = float(c2 - c12) / (n - c1)
            if (p1 != 1) and (p2 != 0):
                l = -2 * (log_l(c12, c1, p) + log_l(c2 - c12, n - c1, p) -
                    - log_l(c12, c1, p1) - log_l(c2 - c12, n - c1, p2))
                if l > threshold:
                    result.append((bigram, l))
            else:
                absolute.append((bigram, self.bigrams_frequency[bigram]))

        absolute.sort(key=lambda tup: tup[1])  # сортируем по частоте, от меньшей к большей
        result.sort(key=lambda tup: tup[1], reverse=True)

        result = absolute + result  # ставим их в начало списка результатов

        with open("results/likelihood_res.txt", "w") as f:
            for b, l in result:
                f.write("{}\n".format(b.encode("utf-8")))

        i = 0
        length = len(result)
        while (i < 100) and (i < length):
            b, l = result[i]
            print u"{}\t{}".format(l, b)
            i += 1

    def mutual_information(self):
        """
        Взаимная информация
        """
        result = list()

        for bigram in self.bigrams_frequency:
            w1, w2 = bigram.split()
            n = self.number_of_words
            p1 = float(self.words_frequency[w1]) / n
            p2 = float(self.words_frequency[w2]) / n
            p12 = float(self.bigrams_frequency[bigram]) / n
            i = log(p12, 2) - (log(p1, 2) + log(p2, 2))
            result.append((bigram, i))
        result.sort(key=lambda tup: tup[1], reverse=True)

        with open("results/mutual_information_res.txt", "w") as f:
            for b, i in result:
                f.write("{}\n".format(b.encode("utf-8")))

        i = 0
        length = len(result)
        while (i < 100) and (i < length):
            b, l = result[i]
            print u"{}\t{}".format(l, b)
            i += 1


def main():
    cf = CollocationFinder("corpus.txt")
    cf.student_test()
    cf.chi_square()
    cf.likelihood()
    cf.mutual_information()


if __name__ == "__main__":
    main()