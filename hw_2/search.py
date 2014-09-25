#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Alibekov"

from index import Index


# Tree realisation class
class TreeNode(object):
    def __init__(self, lexeme):
        self.lexeme = lexeme
        self.children = list()

    def add_child(self, node):
        self.children.append(node)


# Parsing error realisation class
class ParseError(Exception):
    def __init__(self, value=""):
        self.value = value

    def __unicode__(self):
        return self.value


class Parser(object):
    def __init__(self, query):
        self.lexemes = query.replace("(", " ( ").replace(")", " ) ").decode("utf-8").split()
        self.lexemes.append("")  # end of query
        self.pos = 0
        self.tree = self.__disjunction()
        if self.lexemes[self.pos] != "":
            raise ParseError("The error of parsing!")

    def __disjunction(self):
        node = TreeNode("OR")
        node.add_child(self.__conjunction())
        while self.lexemes[self.pos] == "OR":
            self.__next_lexeme()
            node.add_child(self.__conjunction())
        if len(node.children) == 1:
            return node.children[0]
        else:
            return node

    def __conjunction(self):
        node = TreeNode("AND")
        node.add_child(self.__neg())
        while self.lexemes[self.pos] == "AND":
            self.__next_lexeme()
            node.add_child(self.__neg())
        if len(node.children) == 1:
            return node.children[0]
        else:
            return node

    def __neg(self):
        if self.lexemes[self.pos] == "NOT":
            self.__next_lexeme()
            node = TreeNode("NOT")
            node.add_child(self.__term())
            return node
        else:
            return self.__term()

    def __term(self):
        if self.lexemes[self.pos] == "(":
            self.__next_lexeme()
            node = self.__disjunction()
            if self.lexemes[self.pos] != ")":
                raise ParseError("Parenthesis imbalance!")
            self.__next_lexeme()
            return node
        elif self.lexemes[self.pos] in {"OR", "AND", "NOT", ")", ""}:
            raise ParseError("Invalid query!")
        else:
            node = TreeNode(self.lexemes[self.pos].lower())
            self.__next_lexeme()
            return node

    def __next_lexeme(self):
        self.pos += 1


class Search(object):
    def __init__(self, input_file):
        self.index = Index(input_file)
        self.result = list()

    def go(self):
        print "What you are looking for?"
        query = raw_input()
        while query != "QUIT":
            try:
                self.__go_searching(query)
                if len(self.result) == 0:
                    print "\nNothing found for your query. Try another query."
                else:
                    print "\nNumber of documents found: {}".format(len(self.result))
                    count = 0
                    for doc_id in self.result:
                        if count > 10:
                            print "\nShow next documents?"
                            response = raw_input()
                            if response:
                                break
                            else:
                                count = 0
                        print "{0}\t{1}".format(doc_id, self.index.documents[doc_id][:-1].encode("utf-8"))
                        count += 1
            except ParseError as e:
                print e.value
            print "\nWhat you are looking for?"
            query = raw_input()

    def __go_searching(self, query):
        parser = Parser(query)
        self.result = sorted(self.__search(parser.tree))

    def __search(self, tree):
        if tree.lexeme == "OR":
            result = set()
            for child in tree.children:
                result |= self.__search(child)
            return result
        elif tree.lexeme == "AND":
            children = list()
            children_neg = list()
            for child in tree.children:
                if child.lexeme != "NOT":
                    children.append(self.__search(child))
                else:
                    children_neg.append(self.__search(child))
            result = children[0]
            for child in children[1:]:
                result &= child
            for child in children_neg:
                result -= child
            return result
        elif tree.lexeme == "NOT":
            return set(range(len(self.index.documents))) - self.__search(tree.children[0])
        else:
            if tree.lexeme in self.index.terms:
                return set(self.index.terms[tree.lexeme][1])
            else:
                return set()


def main():
    print "Wait for a while. We are building index."
    search = Search("input_text.txt")
    search.go()
    l = list()

if __name__ == "__main__":
    main()
