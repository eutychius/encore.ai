import tensorflow as tf
from os.path import join
import getopt
import sys

import constants as c
from LSTMModel import LSTMModel
from data_reader import DataReader

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.logging.set_verbosity(tf.logging.ERROR)

# https://github.com/dyelax/encore.ai
#Pick an artist – it should be someone with a lot of lyrics. (Over 100,000 words).
#Collect all of the artist's lyrics from your favorite lyrics website. Save each song as a text file in data/artist_name/. We recommend leaving newlines in as a special token so that the network will learn line and stanza breaks.
#Train by navigating to the code directory and running python runner.py -a <artist_name> -m <model_save_name>.
#Our models were all trained for 30,000 steps.
#Generate new songs by running
#python runner.py -a <artist_name> -l ../save/models/<model_save_name>/<ckpt_file> -t.
#Optional: If you would like to specify "prime text" – the initial text that the model will generate from – pass in a string with the -p flag.
#Share your trained models with us so we can feature them on our website! Create an issue with a link to a public Dropbox or Google Drive containing your model's .ckpt file.
class LyricGenRunner:
    def __init__(self, model_load_path, artist_name, test, prime_text):
        """
        Initializes the Lyric Generation Runner.

        @param model_load_path: The path from which to load a previously-saved model.
                                Default = None.
        @param artist_name: The name of the artist on which to train. (Used to grab data).
                            Default = 'kanye_west'
        @param test: Whether to test or train the model. Testing generates a sequence from the
                     provided model and artist. Default = False.
        @param prime_text: The text with which to start the test sequence.
        """

        self.sess = tf.Session()
        self.artist_name = artist_name

        print('Process data...')
        self.data_reader = DataReader(self.artist_name)
        self.vocab = self.data_reader.get_vocab()

        print('Init model...')
        self.model = LSTMModel(self.sess,
                               self.vocab,
                               c.BATCH_SIZE,
                               c.SEQ_LEN,
                               c.CELL_SIZE,
                               c.NUM_LAYERS,
                               test=test)

        print('Init variables...')
        self.saver = tf.train.Saver(max_to_keep=None)
        self.sess.run(tf.global_variables_initializer())

        # if load path specified, load a saved model
        if model_load_path is not None:
            self.saver.restore(self.sess, model_load_path)
            print('Model restored from ' + model_load_path)

        if test:
            self.test(prime_text)
        else:
            self.train()

    def train(self):
        """
        Runs a training loop on the model.
        """
        while True:
            inputs, targets = self.data_reader.get_train_batch(c.BATCH_SIZE, c.SEQ_LEN)

            feed_dict = {self.model.inputs: inputs, self.model.targets: targets}
            global_step, loss, _ = self.sess.run([self.model.global_step,
                                                  self.model.loss,
                                                  self.model.train_op],
                                                 feed_dict=feed_dict)

            print('Step: %d | loss: %f' % (global_step, loss))
            if global_step % c.MODEL_SAVE_FREQ == 0:
                print('Saving model...')
                self.saver.save(self.sess, join(c.MODEL_SAVE_DIR, self.artist_name + '.ckpt'),
                                global_step=global_step)

    def test(self, prime_text):
        """
        Generates a text sequence.
        """
        # generate and save sample sequence
        sample = self.model.generate(prime=prime_text)

        print(sample)


def main():
    load_path = None
    artist_name = 'kanye_west'
    test = False
    prime_text = None

    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'l:m:a:p:s:t', ['load_path=', 'model_name=',
                                                            'artist_name=', 'prime=', 'seq_len',
                                                            'test', 'save_freq='])
    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-l', '--load_path'):
            load_path = arg
        if opt in ('-m', '--model_name'):
            c.set_save_name(arg)
        if opt in ('-a', '--artist_name'):
            artist_name = arg
        if opt in ('-p', '--prime'):
            prime_text = arg
        if opt in ('-s', '--seq_len'):
            c.SEQ_LEN = arg
        if opt in ('-t', '--test'):
            test = True
        if opt == '--save_freq':
            c.MODEL_SAVE_FREQ = int(arg)

    LyricGenRunner(load_path, artist_name, test, prime_text)


if __name__ == '__main__':
    main()
