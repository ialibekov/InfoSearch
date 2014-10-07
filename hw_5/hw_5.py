#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"


def is_cyrillic(s):
    return not all(ord(c) < 300 for c in s)


class LM(object):
    def __init__(self, input_text):
        self.words_frequency = dict()
        self.bigrams_frequency = dict()
        self.trigrams_frequency = dict()
        self.number_of_words = 0
        self.number_of_bigrams = 0
        self.number_of_trigrams = 0

        with open(input_text, "r") as f:
            for i, line in enumerate(f, start=1):
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
                        words_list = list()

                if i % 1000 == 0:
                    print "Computing line {}".format(i)
            self.v = len(self.words_frequency)
            print "total words     = {:7}".format(self.number_of_words)
            print "unique words    = {:7}".format(self.v)
            print "total bigrams   = {:7}".format(self.number_of_bigrams)
            print "unique bigrams  = {:7}".format(len(self.bigrams_frequency))
            print "total trigrams  = {:7}".format(self.number_of_trigrams)
            print "unique trigrams = {:7}".format(len(self.trigrams_frequency))

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
        for e, t in sorted(self.trigrams_frequency.items(), key=lambda tup: -tup[1])[:10]:
            print e
        while True:
            p = 1
            s = raw_input("Enter sentence to calculate probability?\n") + "."
            s = s.replace(".", " . ").replace(",", " , ").replace(":", " : ").replace(";", " ; ").replace("?", " ? ")\
                .replace("!", " ! ").replace("(", " ( ").replace(")", " ) ").replace("--", " -- ").replace(".", " . ")
            words_list = list()
            for lexeme in s.split():
                # проверка, что лексема не является знаком пунктуации
                lexeme = lexeme.translate(None, '.,?!:;()"\'').replace("--", "").decode("utf-8").strip().lower()
                if lexeme:
                    words_list.append(lexeme)
                else:
                    n = len(words_list)
                    if n > 2:
                        w1 = words_list[0]
                        w2 = words_list[1]
                        w3 = words_list[2]
                        p *= self.__p_lid(w1) * self.__p_lid(w1, w2) * self.__p_lid(w1, w2, w3)
                        w1, w2 = w2, w3
                        for w3 in words_list[3:]:
                            p *= self.__p_lid(w1, w2, w3)
                            w1, w2 = w2, w3
                    elif n == 2:
                        w1 = words_list[0]
                        w2 = words_list[1]
                        p *= self.__p_lid(w1) * self.__p_lid(w1, w2)
                    elif n == 1:
                        w1 = words_list[0]
                        p *= self.__p_lid(w1)
                    words_list = list()
            print "P = {}".format(p)


def main():
    lm = LM("corpus.txt")
    lm.run()


if __name__ == "__main__":
    main()