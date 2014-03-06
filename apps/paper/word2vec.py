#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on March 6, 2014

@author: Chunwei Yan @ PKU
@mail:  yanchunwei@outlook.com

generate word vectors using word2vec from project gensim
'''
from __future__ import division

from gensim.models.word2vec import Word2Vec



class Trainer(object):
    def __init__(self, sentences):
        self.word2vec = Word2Vec(sentences, size=100, window=5, min_count=0, workers=4)

    def get_word_evc(self, word):
        '''
        :parameters:
            word: string
        :return: array of float
            word vector generated by word2vec
        '''
        return self.word2vec.get(word)

    def model_tofile(self, filename):
        print 'save model to file:\t', filename
        self.word2vec.save(filename)

    def model_fromfile(self, filename):
        print 'load model from file:\t', filename
        self.word2vec = Word2Vec.load(filename)




if __name__ == "__main__":
    pass
