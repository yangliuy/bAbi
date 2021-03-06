# -*- coding: utf-8 -*-
import sys

from DataProcessor.SICK import SICK
from DataProcessor.SNLI import SNLI

__author__ = 'benywon'
from AnswerSelection import IAGru, OAGru_SMALL
from NeuralModel.IAGRU_WORD import IAGRU_WORD
from NeuralModel.OAGRU import OAGRU_small, OAGRU
from TaskBase import TaskBases

__author__ = 'benywon'

SNLI_DATA = 'SNLI'
SICK_DATA = 'SICK'


class RTE(TaskBases):
    def __init__(self, MODEL=IAGru, DATASET=SNLI_DATA, **kwargs):
        TaskBases.__init__(self)
        if kwargs['sample_weight'] is not None:
            self.sample_weight = kwargs['sample_weight']
        else:
            self.sample_weight = 0.
        if DATASET == SNLI_DATA:
            self.Data = SNLI(**kwargs)
            if self.sample_weight > 0:
                self.Data.sample_data(self.sample_weight)
        elif DATASET == SICK_DATA:
            self.Data = SICK(**kwargs)
        if MODEL == IAGru:
            self.Model = IAGRU_WORD(data=self.Data, classfication=True, **kwargs)
        elif MODEL == OAGru_SMALL:
            self.Model = OAGRU_small(data=self.Data, classfication=True, **kwargs)
        else:
            self.Model = OAGRU(data=self.Data, classfication=True, **kwargs)

    def Test(self):
        print '\nstart testing...'
        length = len(self.Data.TEST[0])
        total = 0.
        right = 0.
        for i in xrange(length):
            question = self.Data.TEST[0][i]
            answer_yes = self.Data.TEST[1][i]
            prediction = self.Model.test_function(question, answer_yes)
            true = self.Data.TEST[2][i]
            total += 1
            b = ("Testing:" + str(i) + " in total:" + str(length) + ' output: ' + str(prediction))
            sys.stdout.write('\r' + b)
            if self.IsIndexMatch(prediction, true, self.Data.batch_training):
                right += 1
        precision = right / total
        print '\nPrecision is :\t' + str(precision)
        return precision

    @TaskBases.Train
    def Train(self):
        if self.sample_weight > 0:
            self.Data.sample_data(self.sample_weight)
        precision = self.Test()
        append_name = self.Data.dataset_name + '_Precision_' + str(precision)
        self.Model.save_model(append_name)


if __name__ == '__main__':
    c = RTE(optmizer='adadelta', MODEL=IAGru, DATASET=SNLI_DATA, sample_weight=0.5, batch_training=True, sampling=3,
            RNN_MODE='GRU',
            reload=True,
            Margin=0.15,
            EmbeddingSize=300,
            N_out=3,
            max_batch_size=32,
            use_the_last_hidden_variable=False, epochs=150, Max_length=80,
            N_hidden=150)
    c.Train()
