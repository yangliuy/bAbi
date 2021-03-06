# -*- coding: utf-8 -*-

from NeuralModel.RNN import *
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


def build_model_sample():
    print 'start building model OAGRU sample...'
    In_quesiotion = T.ivector('in_question')
    In_answer_right = T.ivector('in_answer_right')
    In_answer_wrong = T.ivector('in_answer_wrong')
    EmbeddingMatrix = theano.shared(np.asanyarray(wordEmbedding, dtype='float64'), name='WordEmbedding', )
    in_question_embedding = EmbeddingMatrix[In_quesiotion]
    in_answer_right_embedding = EmbeddingMatrix[In_answer_right]
    in_answer_wrong_embedding = EmbeddingMatrix[In_answer_wrong]
    # this is the shared function

    if RNN_MODE == 'GRU':
        forward = GRU(N_hidden=N_hidden, N_in=EmbeddingSize)
        backward = GRU(N_hidden=N_hidden, N_in=EmbeddingSize, backwards=True)
    elif RNN_MODE == 'LSTM':
        forward = GRU(N_hidden=N_hidden, N_in=EmbeddingSize)
        backward = GRU(N_hidden=N_hidden, N_in=EmbeddingSize, backwards=True)
    else:
        forward = RNN(N_hidden=N_hidden, N_in=EmbeddingSize)
        backward = RNN(N_hidden=N_hidden, N_in=EmbeddingSize, backwards=True)

    def get_lstm_representation(In_embedding):
        forward.build(In_embedding)
        backward.build(In_embedding)
        lstm_forward = forward.get_hidden()
        lstm_bacward = backward.get_hidden()
        return T.concatenate([lstm_forward, lstm_bacward], axis=1)

    question_lstm_matrix = get_lstm_representation(in_question_embedding)
    answer_yes_lstm_matrix = get_lstm_representation(in_answer_right_embedding)
    answer_no_lstm_matrix = get_lstm_representation(in_answer_wrong_embedding)
    if max_ave_pooling == 'ave':
        Oq = T.mean(question_lstm_matrix, axis=0)
    else:
        Oq = T.max(question_lstm_matrix, axis=0)
    Wam = theano.shared(sample_weights(2 * N_hidden, 2 * N_hidden), name='Wam')
    Wms = theano.shared(rng.uniform(-0.3, 0.3, size=(2 * N_hidden)), name='Wms')
    Wqm = theano.shared(sample_weights(2 * N_hidden, 2 * N_hidden), name='Wqm')

    def get_final_result(answer_lstm_matrix):
        if not attention:
            Oa = T.mean(answer_lstm_matrix, axis=0)
        else:
            WqmOq = T.dot(Wqm, Oq)

            Saq_before_softmax = T.nnet.sigmoid(T.dot(answer_lstm_matrix, Wam) + WqmOq)

            Saq = T.nnet.softmax(T.dot(Saq_before_softmax, Wms))
            Oa = T.dot(T.flatten(Saq), answer_lstm_matrix)

        return Oa

    oa_yes = get_final_result(answer_yes_lstm_matrix)
    oa_no = get_final_result(answer_no_lstm_matrix)

    all_params = forward.get_parameter()
    all_params.extend(backward.get_parameter())

    predict_yes = cosine(oa_yes, Oq)
    predict_no = cosine(oa_no, Oq)

    margin = predict_yes - predict_no
    loss = T.maximum(0, Margin - margin)
    our_parameter = [Wam, Wms, Wqm]
    if attention:
        all_params.extend(our_parameter)

    # if Train_embedding:
    #     all_params.append(EmbeddingMatrix)
    # parameter = all_params
    # print 'calc parameters'

    # updates = get_update(loss=loss)
    # loss = add_l1_l2_norm(loss=loss)
    print 'compiling functions'

    train = theano.function([In_quesiotion, In_answer_right, In_answer_wrong],
                            outputs=oa_yes,
                            on_unused_input='ignore',
                            # updates=updates,
                            allow_input_downcast=True)

    return train


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
            WqmOq = T.dot(question_representation, Wqm)
            Saq_before_softmax = T.nnet.sigmoid(T.dot(answer_lstm_matrix, Wam) + WqmOq)
            Saq = T.nnet.softmax(T.dot(Saq_before_softmax, Wms).T)
            Oa = T.batched_dot(Saq, answer_lstm_matrix.dimshuffle(1, 0, 2))
        return Oa

    all_params = forward.get_parameter()
    all_params.extend(backward.get_parameter())
    question_representations = get_output(question_lstm_matrix)
    oa_yes = get_final_result(answer_yes_lstm_matrix, question_representations)
    oa_no = get_final_result(answer_no_lstm_matrix, question_representations)

    classfication = True
    N_out = 3
    if classfication:
        if N_out > 2:
            W1 = theano.shared(sample_weights(2 * N_hidden, 2 * N_hidden), name='w1')
            W2 = theano.shared(sample_weights(2 * N_hidden, 2 * N_hidden), name='w2')
            representation = T.tanh(T.dot(question_representations,W1) + T.dot(oa_yes,W2))
            Wout = theano.shared(sample_weights(2 * N_hidden, N_out), name='Wout')
            prediction = T.nnet.softmax_graph(T.dot(representation, Wout))
            loss = T.nnet.categorical_crossentropy(prediction, In_answer_wrong)
            prediction_label = T.argmax(prediction, axis=1)
            # all_params.append(Wout)
            pass
        else:  # we can also use cosine similarity and transfer it into distribution
            Wout = theano.shared(sample_weights(4 * N_hidden, N_out), name='Wout')
            representation = T.concatenate([question_representations, oa_yes], axis=1)
            prediction = T.nnet.softmax_graph(T.dot(representation, Wout))
            loss = T.nnet.categorical_crossentropy(prediction, In_answer_wrong)
            prediction_label = T.argmax(prediction, axis=1)
            all_params.append(Wout)
            loss = T.mean(loss)
    else:
        predict_yes, _ = theano.scan(cosine, sequences=[oa_yes, question_representations])
        predict_no, _ = theano.scan(cosine, sequences=[oa_no, question_representations])

        margin = predict_yes - predict_no
        loss = T.mean(T.maximum(0, Margin - margin))

    # self.parameter = all_params
    # updates = get_update(loss=loss)
    # loss = add_l1_l2_norm(loss=loss)

    print 'start compile function...'
    train = theano.function([In_quesiotion, In_answer_right, In_answer_wrong],
                            outputs=[loss,prediction_label],
                            # updates=updates,
                            on_unused_input='ignore',
                            allow_input_downcast=True)

    test = theano.function([In_quesiotion, In_answer_right],
                           outputs=In_quesiotion,
                           on_unused_input='ignore',
                           allow_input_downcast=True)
    print 'build model done!'
    return train


question = np.random.random_integers(1, 8, size=(5, 12))
yes = np.random.random_integers(1, 23, size=(5, 9))
no = np.asanyarray([[0, 0, 1] for x in range(5)])

train = build_model_batch()
cc = train(question, yes, no)
print cc
