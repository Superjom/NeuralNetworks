#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
'''
Created on Feb 25, 2014

@author: Chunwei Yan @ PKU
@mail:  yanchunwei@outlook.com
'''
from __future__ import division
import sys
sys.path.append('..')
sys.path.append('../../')
import time
from utils import Timeit
from dataset import *
from models.stacked_autoencoder import StackedAutoEncoder
from exec_frame import ExecFrame, BaseModel


'''
class Trainer(object):
    def __init__(self, pk_data_ph):
        #self.dataset = Dataset(pk_data_ph = pk_data_ph)
        self._init()

    def _init(self):
        #self.dataset.fromfile()
        #self.trainset, self.validset = self.dataset.trans_data_type()
        self.trainset  = load_dataset('data/sample-3000.pk')
        #print 'trainset:'
        #print self.trainset
        # train the model
        records, labels = self.trainset
        #records = numpy.array(records).astype(theano.config.floatX)
        #labels = numpy.array(labels)

        n_records, n_features = records.shape

        self.sA = StackedAutoEncoder(
            n_visible = n_features,
            hidden_struct = [500, 200],
            n_output = 10,
            corrupt_levels = [0.03, 0.03],
            learning_rate = 0.02,
            )

    def __call__(self):
        records, labels = self.trainset
        timeit = Timeit(time.time())
        for i in range(20):
            self.sA.pretrain(records, n_iters=1000, batch_size=400)
            timeit.print_time()
            self.sA.finetune(records, labels, n_iters=800, batch_size=400)
        timeit.print_time()
'''


# implentment interfaces of BaseModel

class _PretrainLayer(BaseModel):
    '''
    a layer execute framework for pretrain
    '''
    def __init__(self, model, trainset, layer_no, batch_size=400):
        self.model = model
        self.trainset = trainset
        self.pretrain_fns = []
        # id of layer
        self.layer_no = layer_no
        self.batch_size = batch_size

    def train_iter(self):
        if not self.pretrain_fns:
            self.pretrain_fns = self.model.compile_pretrain_funcs()
        records, labels = self.trainset
        n_records = records.shape[0]
        n_batches = int(n_records / self.batch_size)

        for rid in xrange(n_batches):
            costs = []
            x = records[rid * self.batch_size: (rid+1) * self.batch_size]
            c = self.pretrain_fns[self.layer_no](x) 
            costs.append(c)

        cost = numpy.array(costs).mean()
        print 'pretraining l %d\tcost\t%f' % (
                    self.layer_no, cost)
        return cost


class _FinetuneLayer(BaseModel):
    '''
    a layer execute framework for pretrain
    '''
    def __init__(self, model, trainset, batch_size=400):
        self.model = model
        self.trainset = trainset
        self.batch_size = batch_size
        self.train_fn = None

    def train_iter(self):
        if not self.train_fn:
            self.train_fn, self.predict_fn = self.model.compile_finetune_funcs()
        records, labels = self.trainset
        n_records = records.shape[0]
        n_batches = int(n_records / self.batch_size)
        costs = []
        for i in xrange(n_batches):
            x, y = records[i*self.batch_size: (i+1)*self.batch_size], labels[i*self.batch_size: (i+1)*self.batch_size]
            cost = self.train_fn(x, y)
            costs.append(cost)
        cost = numpy.array(costs).mean()
        print 'fineture error:\t%f' % cost
        return cost

    def get_model(self):
        return self.model


class _PretrainLayerExec(ExecFrame):
    def __init__(self, model, layer_no,
            batch_size=400,
            model_root="", 
            n_iters=1000,
            dataset=None,
            window=5, tolerance=0.005):

        _model = _PretrainLayer(
            model = model, 
            trainset = dataset,
            layer_no = layer_no,
            batch_size = batch_size,
            )

        ExecFrame.__init__(self,
            model = _model,
            model_root = model_root,
            n_iters = n_iters,
            n_step2save = -1,
            window = window,
            tolerance = tolerance
            )


class _FinetuneLayerExec(ExecFrame):
    def __init__(self, model, model_root="", 
            n_iters=1000, n_step2save=100,
            dataset=None,
            window=5, tolerance=0.005,
            batch_size=400):

        _model = _FinetuneLayer(
            model = model,
            trainset = dataset,
            batch_size = batch_size,
            )

        ExecFrame.__init__(self,
            model = _model,
            model_root = model_root,
            n_iters = n_iters,
            n_step2save = n_step2save,
            window = window,
            tolerance = tolerance
            )

class Main(object):
    def __init__(self, pk_data_ph=None,
            hidden_struct = [],
            corrupt_levels = [0.01, 0.03],
            learning_rate = 0.02,
            batch_size = 400,
            n_pretrain_iters = 800,
            n_finetune_iters = 800,
            window = 10,
            tolerance = 0.002,
            model_root = "_models",
            n_turns = 4,
            ):
        self.pk_data_ph = pk_data_ph
        self.hidden_struct = hidden_struct
        print 'self.hidden_struct:', self.hidden_struct
        self.corrupt_levels = corrupt_levels,
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.n_pretrain_iters = n_pretrain_iters
        self.n_finetune_iters = n_finetune_iters
        self.window = window
        self.model_root = model_root
        self.tolerance = tolerance
        self.n_turns = n_turns
        self._init()
        self._init_exec()

    def _init(self):
        self.trainset  = load_dataset(self.pk_data_ph)
        records, labels = self.trainset

        n_records, n_features = records.shape

        self.sA = StackedAutoEncoder(
            n_visible = n_features,
            hidden_struct = self.hidden_struct,
            n_output = 10,
            corrupt_levels = self.corrupt_levels,
            learning_rate = self.learning_rate,
            )

    def _init_exec(self):
        # for hidden layers
        self.hidden_layer_execs = []
        for no,layer in enumerate(self.sA.hidden_layers):
            _exec = _PretrainLayerExec(
                model = self.sA,
                layer_no = no,
                batch_size = self.batch_size,
                n_iters = self.n_pretrain_iters,
                dataset = self.trainset,
                window = self.window,
                tolerance = self.tolerance,
                )
            self.hidden_layer_execs.append(_exec)
        # for output layer
        _exec = _FinetuneLayerExec(
            model = self.sA,
            model_root = self.model_root,
            window = self.window,
            n_iters = self.n_finetune_iters,
            dataset = self.trainset,
            tolerance = self.tolerance,
            batch_size = self.batch_size,
            )
        self.output_layer_exec = _exec

    def _pretrain(self):
        for no, exe in enumerate(self.hidden_layer_execs):
            exe.run()

    def _finetune(self):
        self.output_layer_exec.run()

    def __call__(self):
        sys.stdout.write("begin to output...")
        records, labels = self.trainset
        timeit = Timeit(time.time())
        for i in range(self.n_turns):

            self._pretrain()

            timeit.print_time()

            self._finetune()
        timeit.print_time()



class Trainer(object):
    def __init__(self, pk_data_ph=None):
        self._init()
        self._init_exec()

    def _init(self):
        self.trainset  = load_dataset('data/train-0.800000.pk')
        records, labels = self.trainset

        n_records, n_features = records.shape

        self.sA = StackedAutoEncoder(
            n_visible = n_features,
            hidden_struct = [450],
            n_output = 10,
            corrupt_levels = [0.01, 0.03],
            learning_rate = 0.02,
            )

    def _init_exec(self):
        # for hidden layers
        self.hidden_layer_execs = []
        for no,layer in enumerate(self.sA.hidden_layers):
            _exec = _PretrainLayerExec(
                model = self.sA,
                layer_no = no,
                batch_size = 400,
                n_iters = 800,
                dataset = self.trainset,
                window = 10,
                tolerance = 0.002,
                )
            self.hidden_layer_execs.append(_exec)
        # for output layer
        _exec = _FinetuneLayerExec(
            model = self.sA,
            model_root = '_models/1_450_sparce/',
            window = 10,
            n_iters = 800,
            dataset = self.trainset,
            tolerance = 0.002,
            batch_size = 400,
            )
        self.output_layer_exec = _exec

    def _pretrain(self):
        for no, exe in enumerate(self.hidden_layer_execs):
            exe.run()

    def _finetune(self):
        self.output_layer_exec.run()

    def __call__(self):
        sys.stdout.write("begin to output...")
        records, labels = self.trainset
        timeit = Timeit(time.time())
        for i in range(8):

            self._pretrain()

            timeit.print_time()

            self._finetune()
        timeit.print_time()




if __name__ == '__main__':
    #dataset = Dataset('./trainset.csv', './norm_float_dataset.pk')
    #dataset.load_ori_dataset()
    #dataset.load_dataset_to_norm_float()
    #dataset.tofile()
    #dataset.fromfile()
    #trainset, validset = dataset.trans_data_type()
    #print trainset.shape, validset.shape
    trainer = Trainer(
        pk_data_ph = './norm_float_dataset.pk'
        )
    trainer()
