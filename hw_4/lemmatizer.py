#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from pymystem3 import Mystem


def main():
    stem = Mystem()
    with open("corpus.txt", "r") as f_input:
        with open("lemmatized_corpus.txt", "w") as f:
            for i, line in enumerate(f_input):
                f.write(" ".join(stem.lemmatize(line)))
                if i % 100 == 0:
                    print i
                i += 1


if __name__ == "__main__":
    main()