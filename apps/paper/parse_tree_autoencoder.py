#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on March 7, 2014

@author: Chunwei Yan @ PKU
@mail:  yanchunwei@outlook.com

train recursive autoencoder based on parse trees generated by Standford Parser
'''
from __future__ import division
import sys
import theano
sys.path.append('..')
sys.path.append('../../')
import numpy 
from paper import config as cg
from models.recursive_autoencoder.binary_tree_autoencoder import BinaryTree, BinaryTreeAutoencoder
from syntax_tree.parse_tree import SyntaxTreeParser

class ParseTreeAutoencoder(object):
    '''
    based on SyntaxTreeParser and BinaryTree
    '''
    def __init__(self, word2vec):
        '''
        :parameters:
            word2vec: pre-trained word2vec model
        '''
        self.word2vec = word2vec
        self.len_vector = cg.LEN_WORD_VECTOR
        self.bta = BinaryTreeAutoencoder(
            len_vector = self.len_vector,
            )
        # binary autoencoder
        self.bae = self.bta.bae

    def train_with_tree(self, parse_tree):
        '''
        :parameters:
            parse_tree: string
        '''
        tree = self.create_tree(parse_tree)
        bt = BinaryTree(tree.root, self.bae)
        return self.bta.train_with_tree(bt)

    def create_tree(self, parse_tree):
        '''
        parse a line and return a tree

        :parameters:
            parse_tree: string

        :returns:
            syntax_tree : object of SyntaxTreeParser
        '''
        syntax_tree = SyntaxTreeParser(parse_tree)
        # init leaf node's vector
        syntax_tree.init_leaf_vec(self.word2vec)
        return syntax_tree





if __name__ == "__main__":
    from _word2vec import Trainer as Word2Vec
    data_ph = "./data/syntax_trees.txt"
    trees = []
    with open(data_ph) as f:
        while True:
            line = f.readline()
            if not line:break
            trees.append(line)

    _word2vec = Word2Vec()
    _word2vec.model_fromfile('data/models/2.w2v')
    pa = ParseTreeAutoencoder(_word2vec)

    for tree in trees:
        #print 'train:', tree
        cost = pa.train_with_tree(tree)
        print 'cost', cost


