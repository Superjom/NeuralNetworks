#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Feb 22, 2014

@author: Chunwei Yan @ PKU
@mail:  yanchunwei@outlook.com
'''
import theano
import numpy
from theano import tensor as T

rng = numpy.random
#theano.config.compute_test_value = 'warn'
theano.config.compute_test_value = 'off'
#theano.config.device = 'cpu'
theano.config.floatX = 'float32'
theano.config.mode = 'FAST_COMPILE'
from exec_frame import ExecFrame, BaseModel


class SoftmaxRegression(object):
    def __init__(self, input=None, output=None, 
                    n_features=500, 
                    n_states=10, learning_rate=0.01):

        self.n_features = n_features
        self.n_states = n_states
        # x is a vector
        self.x = input
        if not self.x:
            self.x = T.fvector('x')
        # y is a label(0 1 2 3 ..)
        self.y = output
        if not self.y:
            self.y = T.bscalar('y')
        # test value
        #self.x.tag.test_value = rng.random(n_features).astype(
        #    theano.config.floatX)
        #self.y.tag.test_value = 3
        #self.y = T.cast(y, 'int32')
        
        self.b = theano.shared(numpy.zeros((n_states),
            dtype=theano.config.floatX),
            name = 'b',
            borrow = True,
            )
        self.W = theano.shared(
            value = numpy.zeros(( n_features, n_states),
                dtype=theano.config.floatX),
            name = 'W',
            borrow = True,
            )

        self.p_y_given_x = T.nnet.softmax(
                 T.dot(self.W, self.x)  + self.b)
        # get the max index
        self.y_pred = T.argmax(self.p_y_given_x, axis=1)
        self.get_y_pred = theano.function(
            inputs = [self.x],
            allow_input_downcast=True,
            outputs = self.y_pred)

        self.learning_rate = learning_rate

        self.params = [self.W, self.b]


    def negative_log_likelihood(self, y):
        '''
        y is the right target
        '''
        self.get_p_y_given_x = \
            theano.function(
                inputs = [self.x],
                allow_input_downcast=True,
                outputs = self.p_y_given_x)

        # - likelihood
        loss = - T.mean(T.log(self.p_y_given_x[0][y]))
        return loss

    def errors(self, y):
        '''
        '''
        # neq : not equal
        return T.mean(T.neq(self.y_pred, y))

    def train(self, set_x, set_y, n_iters=1000):
        n_records = set_x.shape[0]

        self.p_y_given_x = T.nnet.softmax(
                 T.dot(self.x, self.W)  + self.b)
       
        train_model = self.compile_train_fn()

        #theano.printing.pydotprint(train_model)
        for no in xrange(n_iters):
            costs = []
            for i in xrange(n_records):
                x = numpy.array(set_x[i]).astype(
                        theano.config.floatX)
                y = set_y[i]
                #print 'x', x
                #print 'y', y
                #print 'get_p_y_given_x'
                #print self.get_p_y_given_x(x)
                cost = train_model(x, y)
                '''
                if no == (n_iters - 1):
                    y_pred = self.get_y_pred(x)
                    y_preds.append(y_pred)
                '''
                costs.append(cost)

            c = numpy.array(costs).mean()
            print no, c
        #print 'target :10'
        #print set_y[:30]
        #print [y[0] for y in y_preds[:30]]
        #print no, c

    def compile_train_fn(self):
        cost = self.negative_log_likelihood(self.y) + 0.01 * T.mean(self.W ** 2)
        gW = T.grad(cost, self.W)
        gb = T.grad(cost, self.b)

        updates = [
            (self.W, self.W - self.learning_rate * gW),
            (self.b, self.b - self.learning_rate * gb)]

        train_model = theano.function(
            inputs = [self.x, self.y],
            updates = updates,
            allow_input_downcast=True,
            outputs = cost)

        predict_model = theano.function(
            inputs = [self.x],
            outputs = T.argmax(self.p_y_given_x, axis=1),
            )

        return train_model, predict_model




class BatchSoftmaxRegression(SoftmaxRegression):
    '''
    a batch version of softmax which runs faster using a GPU
    '''
    def __init__(self, input=None, output=None, 
                    n_features=500, 
                    n_states=10, learning_rate=0.01):
        # init scalars
        # x is a matrix: batch_size X n_features
        # y is a vector: batch_size
        self.x = input
        if not self.x:
            self.x = T.fmatrix('x')
        # y is a label(0 1 2 3 ..)
        self.y = output
        if not self.y:
            self.y = T.lvector('y')
        # init SoftmaxRegression
        SoftmaxRegression.__init__(self,
            input = self.x,
            output = self.y,
            n_features = n_features,
            n_states = n_states,
            learning_rate = learning_rate)

        self.p_y_given_x = T.nnet.softmax(
                 T.dot( self.x, self.W)  + self.b)

    def negative_log_likelihood(self, y):
        '''
        y is the right target
        '''
        self.get_p_y_given_x = \
            theano.function(
                inputs = [self.x],
                allow_input_downcast=True,
                outputs = self.p_y_given_x)

        # - likelihood
        loss = - T.mean(T.log(self.p_y_given_x)[T.arange(y.shape[0]), y])
        return loss


    def train(self, set_x, set_y, batch_size=3, n_iters=1000):
        train_model, predict_model = self.compile_train_fn()

        n_records = set_x.shape[0]

        n_batchs = int(n_records / batch_size)
        #theano.printing.pydotprint(train_model)
        for no in xrange(n_iters):
            costs = []
            for i in xrange(n_batchs):
                x = set_x[ i*batch_size : (i+1) * batch_size]
                y = set_y[ i*batch_size : (i+1) * batch_size]
                #print 'x', x
                #print 'y', y
                cost = train_model(x, y)
                y_pred = predict_model(x)
                print 'y\t', y
                print 'y_pred\t', y_pred
                costs.append(cost.mean())
            c = numpy.array(costs).mean()
            print no, c



class _BatchSoftmaxRegression(BaseModel):
    '''
    a softmax regression class implements BaseModel interfaces
    '''
    def __init__(self, 
            input=None, output=None, 
            n_features=500, n_states=10, learning_rate=0.01,
            # exec paramters
            trainset=None, 
            batch_size = 400): 

        self.model = BatchSoftmaxRegression(
                input=input, 
                output=output, 
                n_features=n_features, 
                n_states=n_states, 
                learning_rate=learning_rate)

        self.trainset = trainset
        self.batch_size = batch_size
        # init
        self._train_fn = None
        self._predict_fn = None

    def train_iter(self):
        records, labels = self.trainset
        if not self._train_fn:
            self._train_fn, self._predict_fn = self.model.compile_train_fn()
        n_records = records.shape[0]

        n_batchs = int(n_records / self.batch_size)
        costs = []
        for i in xrange(n_batchs):
            x = records[ i*self.batch_size : (i+1) * self.batch_size]
            y = labels[ i*self.batch_size : (i+1) * self.batch_size]
            #print 'x', x
            #print 'y', y
            cost = self._train_fn(x, y)
            #y_pred = self._predict_fn(x)
            #print 'y\t', y
            #print 'y_pred\t', y_pred
            costs.append(cost.mean())
        c = numpy.array(costs).mean()
        print  c
        return c

    def predict(self, x):
        if not self._predict_fn:
            self._train_fn, self._predict_fn = self.model.compile_train_fn()
        return self._predict_fn(x)

    def get_model(self):
        return self.model



class _Exec(ExecFrame):
    def __init__(self, model_root="", 
            n_iters=1000, n_step2save=100,
            dataset=None,
            window=5, tolerance=0.005):

        #x_set = rng.randn(50, 30).astype(theano.config.floatX)
        #y_set = rng.randint(size=50, low=0, high=10).astype(theano.config.floatX)

        model = _BatchSoftmaxRegression(
            trainset = dataset,
            batch_size = 40,
            n_features=30, n_states=10,
            )

        ExecFrame.__init__(self,
            model = model,
            model_root = model_root,
            n_iters = n_iters,
            n_step2save = n_step2save,
            window = window,
            tolerance = tolerance
            )






if __name__ == "__main__":
    x_set = rng.randn(500, 30).astype(theano.config.floatX)
    y_set = rng.randint(size=500, low=0, high=10).astype(theano.config.floatX)

    def test_softmax_regression():
        s = SoftmaxRegression(
            n_features=30)
        s.train(x_set, y_set, n_iters=4)

    #test_softmax_regression()

    def test_batch():
        s = BatchSoftmaxRegression(
            n_features=30)

        s.train(x_set, y_set, n_iters=4000, 
                batch_size=6
            )

    #test_batch()
    _exec = _Exec(
        n_iters = 100,
        tolerance = 0.000001,
        model_root = "_models",
        n_step2save = 100,
        dataset=(x_set, y_set,),
        window=16,
        )
    _exec.run()


