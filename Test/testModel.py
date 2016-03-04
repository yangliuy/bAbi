# -*- coding: utf-8 -*-
import numpy as np
import theano.tensor as T
import theano

from RNN import *
from public_functions import *

__author__ = 'benywon'

RNN_MODE = 'GRU'
wordEmbedding = sample_weights(100, 50)
N_hidden = 120
EmbeddingSize = 50
use_the_last_hidden_variable = False
max_ave_pooling = 'ave'
attention = True
Margin = 0.15


def build_model_batch():
    print 'start building model OAGRU batch...'
    In_quesiotion = T.imatrix('in_question')
    In_answer_right = T.imatrix('in_answer_right')
    In_answer_wrong = T.imatrix('in_answer_wrong')
    EmbeddingMatrix = theano.shared(np.asanyarray(wordEmbedding, dtype='float64'), name='WordEmbedding', )
    in_question_embeddings = EmbeddingMatrix[In_quesiotion]
    in_answer_right_embeddings = EmbeddingMatrix[In_answer_right]
    in_answer_wrong_embeddings = EmbeddingMatrix[In_answer_wrong]
    # this is the shared function
    if RNN_MODE == 'GRU':
        forward = GRU(N_hidden=N_hidden, batch_mode=True, N_in=EmbeddingSize)
        backward = GRU(N_hidden=N_hidden, batch_mode=True, N_in=EmbeddingSize, backwards=True)
    elif RNN_MODE == 'LSTM':
        forward = GRU(N_hidden=N_hidden, batch_mode=True, N_in=EmbeddingSize)
        backward = GRU(N_hidden=N_hidden, batch_mode=True, N_in=EmbeddingSize, backwards=True)
    else:
        forward = RNN(N_hidden=N_hidden, batch_mode=True, N_in=EmbeddingSize)
        backward = RNN(N_hidden=N_hidden, batch_mode=True, N_in=EmbeddingSize, backwards=True)

    Wam = theano.shared(sample_weights(2 * N_hidden, 2 * N_hidden), name='Wam')
    Wms = theano.shared(rng.uniform(-0.3, 0.3, size=(2 * N_hidden)), name='Wms')
    Wqm = theano.shared(sample_weights(2 * N_hidden, 2 * N_hidden), name='Wqm')

    def get_gru_representation(In_embedding):
        forward.build(In_embedding)
        backward.build(In_embedding)
        lstm_forward = forward.get_hidden()
        lstm_backward = backward.get_hidden()
        if use_the_last_hidden_variable:
            return T.concatenate([lstm_forward, lstm_backward[::-1]], axis=2)
        else:
            return T.concatenate([lstm_forward, lstm_backward], axis=2)

    question_lstm_matrix = get_gru_representation(in_question_embeddings)
    answer_yes_lstm_matrix = get_gru_representation(in_answer_right_embeddings)
    answer_no_lstm_matrix = get_gru_representation(in_answer_wrong_embeddings)

    def get_output(In_matrix):
        if use_the_last_hidden_variable:
            Oq = In_matrix[-1]
        else:
            if max_ave_pooling == 'ave':
                Oq = T.mean(In_matrix, axis=0)
            else:
                Oq = T.max(In_matrix, axis=0)
        return Oq

    def get_final_result(answer_lstm_matrix, question_representation):
        if not attention:
            Oa = T.mean(answer_lstm_matrix, axis=0)
        else:
            WqmOq = T.dot(Wqm, question_representation)

            # Saq_before_softmax, _ = theano.scan(lambda v: T.tanh(T.dot(v, Wam) + WqmOq), sequences=answer_lstm)
            Saq_before_softmax = T.nnet.sigmoid(T.dot(answer_lstm_matrix, Wam) + WqmOq)
            # then we softmax this layer

            Saq = T.nnet.softmax(T.dot(Saq_before_softmax, Wms))

            HatHat = T.dot(T.diag(T.flatten(Saq)), answer_lstm_matrix)

            Oa = T.sum(HatHat, axis=0)
        return Oa

    question_representation = get_output(question_lstm_matrix)
    # answer_yes_lstm_matrix = get_final_result(in_answer_right_embeddings, question_representation)
    # answer_no_lstm_matrix = get_final_result(in_answer_wrong_embeddings, question_representation)
    #
    # oa_yes = get_output(answer_yes_lstm_matrix)
    # oa_no = get_output(answer_no_lstm_matrix)
    #
    # predict_yes, _ = theano.scan(cosine, sequences=[oa_yes, question_representation])
    # predict_no, _ = theano.scan(cosine, sequences=[oa_no, question_representation])
    #
    # margin = predict_yes - predict_no
    # loss = T.mean(T.maximum(0, Margin - margin))

    all_params = forward.get_parameter()
    all_params.extend(backward.get_parameter())

    parameter = all_params
    # updates = get_update(loss=loss)
    # loss = add_l1_l2_norm(loss=loss)

    print 'start compile function...'
    train = theano.function([In_quesiotion, In_answer_right, In_answer_wrong],
                            outputs=question_representation,
                            # updates=updates,
                            on_unused_input='ignore',
                            allow_input_downcast=True)

    # test = theano.function([In_quesiotion, In_answer_right],
    #                        outputs=predict_yes[0],
    #                        on_unused_input='ignore',
    #                        allow_input_downcast=True)
    print 'build model done!'
    return train


question = np.random.random_integers(1, 8, size=(5, 14))
yes = np.random.random_integers(1, 23, size=(5, 9))
no = np.random.random_integers(1, 83, size=(5, 33))

train = build_model_batch()
cc = train(question, yes, no)
print cc