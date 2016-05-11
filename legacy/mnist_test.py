from deepgraph.graph import *
from deepgraph.solver import *
from deepgraph.nn.core import *
from deepgraph.nn.loss import *
from deepgraph.nn.conv import *
from deepgraph.nn.init import *
from deepgraph.utils.datasets import *

from theano.tensor.nnet import relu

data = load_data("./data/mnist.pkl.gz")

train_x, train_y = data[0]
val_x, val_y = data[1]
batch_size = 600

g = Graph("test")

# Until now, sequence matters to map inputs to compiled model inlets
# In addition, we need to specify the shape we want to have the input in such that deepgraph
# can calculate necessary mem.

data = Data(g, "data", T.matrix, shape=(-1, 1, 28, 28))
label = Data(g, "label", T.ivector, shape=(-1,), config={
    "phase": PHASE_TRAIN
})
conv_0 = data.connect(Conv2D(g, "conv_1", config={
    "channels": 20,
    "kernel": (5, 5),
    "activation": relu,
    "weight_filler": xavier(gain="relu"),
    "bias_filler": constant(0)
}))
pool_0 = conv_0.connect(Pool(g, "pool_0", config={
    "kernel": (2, 2)
}))
lrn_0 = pool_0.connect(LRN(g, "lrn_0"))
conv_1 = lrn_0.connect(Conv2D(g, "conv_2", config={
    "channels": 50,
    "kernel": (5, 5),
    "activation": relu,
    "weight_filler": xavier(gain="relu"),
    "bias_filler": constant(0)
}))
pool_1 = conv_1.connect(Pool(g, "pool_1", config={
    "kernel": (2, 2)
}))
lrn_1 = pool_1.connect(LRN(g, "lrn_1"))
flatten = lrn_1.connect(Flatten(g, "flatten", config={
    "dims": 2
}))
hidden_0 = flatten.connect(Dense(g, "tanh_0", config={
    "out": 500,
    "weight_filler": xavier(),
    "bias_filler": constant(0.0001),
    "activation": T.tanh
}))
soft = hidden_0.connect(Softmax(g, "softmax", config={
    "out": 10,
    "weight_filler": xavier(),
    "bias_filler": constant(0.0001)
}))

argm = soft.connect(Argmax(g, "argmax", config={
    "is_output": True
}))

# Error and loss terms
error = Error(g, "error")
loss = NegativeLogLikelyHoodLoss(g, "loss")
l2 = L2RegularizationLoss(g, "l2", config={"loss_weight": 0})

# Connect losses / errors
soft.connect(loss)
soft.connect(l2)
hidden_0.connect(l2)

argm.connect(error)

label.connect(error)
label.connect(loss)


g.compile(train_inputs=[train_x, train_y], val_inputs=[val_x, val_y], batch_size=batch_size)
log("Starting optimization phase", LOG_LEVEL_INFO)
solver = Solver(lr=0.01)
solver.load(g)
solver.optimize(100)
solver.learning_rate = 0.02
solver.optimize(400)
log("Testing inference", LOG_LEVEL_INFO)
for idx in range(40):
    i_train_x = train_x.get_value()[idx]
    print g.infer([i_train_x.reshape((1, 1, 28, 28))])


