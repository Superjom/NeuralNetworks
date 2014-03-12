#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on March 7, 2014

@author: Chunwei Yan @ PKU
@mail:  yanchunwei@outlook.com

train the autoencoder to merge the word vectors generated by word2vec,
and finally generate the sentence vector.
'''
from __future__ import division
import sys
import theano
sys.path.append('..')
sys.path.append('../../')
import numpy 
from paper import config
from syntax_tree.parse_tree import SyntaxTreeParser
from models.autoencoder import BatchAutoEncoder



class SyntaxTreeAutoencoder(object):
    def __init__(self, word2vec):
        # word2vec model which has been trained before
        self.word2vec = word2vec
        self.syntax_tree_parser = SyntaxTreeParser()
        self.autoencoder = BatchAutoEncoder(
                n_visible = 2 * config.LEN_WORD_VECTOR,
                n_hidden = config.LEN_WORD_VECTOR,
                )
        self.predict_fn = None

    def train(self, syntax_trees):
        '''
        :parameters:
            syntax_tree: list of string
                output of Standford Parser
        '''
        for no,syntax in enumerate(syntax_trees):
            print '.. training %dth tree' % no
            # generate trees
            self.syntax_tree_parser.set_sentence(syntax)
            #self.syntax_tree_parser.draw_graph('tmp.dot')
            # recursively train autoencoder node by node
            try:
                self.train_node(self.syntax_tree_parser.root)
            except Exception,e:
                print "!! error parsing %dth tree"
                print "!! error:", e
                print "!! content:\t%s" % syntax
                print "!! drop this parse tree"

    def train_node(self, node, update_node_vector=True):
        '''
        train the autoencoder with a node  of the syntax tree
        :parameters:
            node: object of Node
            update_node_vector: bool
                just update the node vector without trainning 
        '''
        if not node:
            return
        if node.is_leaf():
            node.vector = self.word2vec.get_word_vec(node.get_word())
        else:
            lvector = self.train_node(node.lchild)
            rvector = self.train_node(node.rchild)
            x = numpy.append(lvector, rvector)
            if not update_node_vector:
                # train the tree node by node, TODO use batch to accelrate the speed?
                self.autoencoder.train_iter(lvector, rvector)
            node.vector = self.get_merged_value(x)
        return node.vector

    def get_merged_value(self, x):
        if not self.predict_fn:
            self.predict_fn = theano.function(
                [self.autoencoder.x],
                self.autoencoder.get_hidden_values(self.autoencoder.x)
                )
        #print 'x', x, len(x)
        x = x.reshape((1, 2*config.LEN_WORD_VECTOR))
        return self.predict_fn(x)

    def get_sentence_vector(self):
        vector = self.syntax_tree_parser.root.vector
        assert vector, "should train and update the tree's autoencoder first"
        return vector







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
    syntax_tree_autoencoder = SyntaxTreeAutoencoder(_word2vec)
    syntax_tree_autoencoder.train(trees)

