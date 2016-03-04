# -*- coding: utf-8 -*-
from ModelBase import ModelBase
import theano.tensor as T
import theano
__author__ = 'benywon'


class IAGRU(ModelBase):
    def __init__(self, max_ave_pooling='ave', use_the_last_hidden_variable=False, Margin=0.1,
                 **kwargs):
        ModelBase.__init__(self, **kwargs)
        self.Margin = Margin
        self.use_the_last_hidden_variable = use_the_last_hidden_variable
        self.max_ave_pooling = max_ave_pooling
        self.model_file_base_path = './model/OAGRU/'
        assert len(self.wordEmbedding) > 0, 'you have not initiate data!!!'
        self.build_model()
        self.print_model_info(model_name='OAGRU')
        self.RNN_MODE = 'GRU'

    @ModelBase.print_model_info
    def print_model_info(self, model_name='OAGRU'):
        """
        remember to add model name when call this function
        :param model_name:
        :return:
        """
        print 'use the last hidden variable as output:\t' + str(self.use_the_last_hidden_variable)
        print 'max or ave pooling?\t' + str(self.max_ave_pooling)
        print 'Embedding size:\t' + str(self.EmbeddingSize)
        print 'dictionary size:\t' + str(self.vocabularySize)
        print 'Margin:\t' + str(self.Margin)
        print 'negative sample size:\t' + str(self.sampling)
        print 'RNN mode:\t' + self.RNN_MODE
    def build_model_sample(self, only_for_test=False):
        print 'start building model IAGRU sample...'
        In_quesiotion = T.ivector('in_question')
        In_answer_right = T.ivector('in_answer_right')
        In_answer_wrong = T.ivector('in_answer_wrong')
        EmbeddingMatrix = theano.shared(np.asanyarray(self.wordEmbedding, dtype='float64'), name='WordEmbedding', )
        in_question_embedding = EmbeddingMatrix[In_quesiotion]
        in_answer_right_embedding = EmbeddingMatrix[In_answer_right]
        in_answer_wrong_embedding = EmbeddingMatrix[In_answer_wrong]
        # this is the shared function

        forward = GRU(N_hidden=self.N_hidden, N_in=self.EmbeddingSize)
        backward = GRU(N_hidden=self.N_hidden, N_in=self.EmbeddingSize, backwards=True)

        def get_gru_representation(In_embedding):
            forward.build(In_embedding)
            backward.build(In_embedding)
            lstm_forward = forward.get_hidden()
            lstm_backward = backward.get_hidden()
            if self.use_the_last_hidden_variable:
                return T.concatenate([lstm_forward, lstm_backward[::-1]], axis=1)
            else:
                return T.concatenate([lstm_forward, lstm_backward], axis=1)

        def trans_representationfromquestion(In_embedding, question):
            sigmoid = sigmoids(T.dot(T.dot(In_embedding, attention_projection), question))
            transMatrix = In_embedding.T * sigmoid
            return get_gru_representation(transMatrix.T)

        def get_output(In_matrix):
            if self.use_the_last_hidden_variable:
                Oq = In_matrix[-1]
            else:
                if self.max_ave_pooling == 'ave':
                    Oq = T.mean(In_matrix, axis=0)
                else:
                    Oq = T.max(In_matrix, axis=0)
            return Oq

        attention_projection = theano.shared(sample_weights(self.EmbeddingSize, 2 * self.N_hidden),
                                             name='attention_projection')
        question_lstm_matrix = get_gru_representation(in_question_embedding)

        question_representation = get_output(question_lstm_matrix)

        answer_yes_lstm_matrix = trans_representationfromquestion(in_answer_right_embedding, question_representation)
        answer_no_lstm_matrix = trans_representationfromquestion(in_answer_wrong_embedding, question_representation)

        oa_yes = get_output(answer_yes_lstm_matrix)
        oa_no = get_output(answer_no_lstm_matrix)

        predict_yes = cosine(oa_yes, question_representation)
        predict_no = cosine(oa_no, question_representation)

        margin = predict_yes - predict_no
        loss = T.maximum(0, self.Margin - margin)

        all_params = forward.get_parameter()
        all_params.extend(backward.get_parameter())
        all_params.append(attention_projection)
        self.parameter = all_params

        updates = self.get_update(loss=loss)
        loss = self.add_l1_l2_norm(loss=loss)

        print 'start compile function...'

        train = theano.function([In_quesiotion, In_answer_right, In_answer_wrong],
                                outputs=loss,
                                updates=updates,
                                allow_input_downcast=True)
        test = theano.function([In_quesiotion, In_answer_right],
                               outputs=predict_yes,
                               on_unused_input='ignore')
        print 'build model done!'
        return train, test
