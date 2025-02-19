#! /usr/bin/env python

import IPython

import pooltool as pt

ipython = IPython.get_ipython()

get_args = lambda: [np.random.rand(9).reshape((3, 3)), 0.0285, 0.18, 9.8]


def old():
    pt.physics.get_slide_time(*get_args())


def new():
    pt.physics.get_slide_time_fast(*get_args())


new()

ipython.magic("timeit old()")
ipython.magic("timeit new()")

args = get_args()
output1 = pt.physics.get_slide_time(*args)
output2 = pt.physics.get_slide_time_fast(*args)

np.testing.assert_allclose(output1, output2)
