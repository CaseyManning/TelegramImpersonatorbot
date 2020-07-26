#!/usr/bin/env python3

import json
import os
import numpy as np
import tensorflow as tf
import time

import model
import sample
import encoder

model_name = '117M_current'

seed = None
nsamples = 1
batch_size = 1
length = 100
temperature = 0.8
top_k = 40

if batch_size is None:
    batch_size = 1
assert nsamples % batch_size == 0

enc = None
hparams = None

def init():
    global enc
    global hparams
    global length
    enc = encoder.get_encoder(model_name)
    hparams = model.default_hparams()
    with open(os.path.join(model_name, 'hparams.json')) as f:
        hparams.override_from_dict(json.load(f))

    if length is None:
        length = hparams.n_ctx // 2
    elif length > hparams.n_ctx:
        raise ValueError(
            "Can't get samples longer than window size: %s" % hparams.n_ctx)


def get_reply(text):

    start = time.time()

    with tf.Session(graph=tf.Graph()) as sess:
        context = tf.placeholder(tf.int32, [batch_size, None])
        np.random.seed(seed)
        tf.set_random_seed(seed)
        output = sample.sample_sequence(
            hparams=hparams, length=length,
            context=context,
            batch_size=batch_size,
            temperature=temperature, top_k=top_k
        )

        saver = tf.train.Saver()
        ckpt = tf.train.latest_checkpoint(os.path.join(model_name))
        saver.restore(sess, ckpt)

        raw_text = "other person: " + text + "\n casey:"
        context_tokens = enc.encode(raw_text)
        generated = 0
        for _ in range(nsamples // batch_size):
            out = sess.run(output, feed_dict={
                context: [context_tokens for _ in range(batch_size)]
            })[:, len(context_tokens):]
            for i in range(batch_size):
                generated += 1
                text = enc.decode(out[i])
                print("——————————————Generated reply in " +
                      str(time.time() - start) + " seconds——————————————")
                # print('length variable: ' + str(length))
                print(text)
                return text


# if __name__ == '__main__':
#     fire.Fire(interact_model)
