import theano.tensor as T

from deepgraph.node import Node, register_node
from deepgraph.constants import *

__docformat__ = 'restructedtext en'


@register_node
class NegativeLogLikelyHoodLoss(Node):
    """
    Compute the negative log likelyhood loss of a given input
    Loss weight specifies to which degree the loss is considered during the update phases
    """
    def __init__(self, graph, name, inputs=[],config={}):
        """
        Constructor
        :param graph: Graph
        :param name: String
        :param config: Dict
        :return: Node
        """
        super(NegativeLogLikelyHoodLoss, self).__init__(graph, name, inputs=inputs, config=config)
        self.is_loss = True

    def setup_defaults(self):
        super(NegativeLogLikelyHoodLoss, self).setup_defaults()
        self.conf_default("loss_weight", 1.0)

    def alloc(self):
        self.output_shape = (1,)

    def forward(self):
        if len(self.inputs) != 2:
            raise AssertionError("This node needs exactly two inputs to calculate loss")
        # Get the label
        if self.inputs[0].is_data:
            label = self.inputs[0].expression
            pred = self.inputs[1].expression
        else:
            label = self.inputs[1].expression
            pred = self.inputs[0].expression
        # Define our forward function
        self.expression = -T.mean(T.log(pred)[T.arange(label.shape[0]), label])


@register_node
class L1RegularizationLoss(Node):
    """
    L1 regularization node for adjacent fc layers
    """
    def __init__(self, graph, name, inputs=[],config={}):
        """
        Constructor
        :param graph: Graph
        :param name: String
        :param config: Dict
        :return: Node
        """
        super(L1RegularizationLoss, self).__init__(graph, name, inputs=inputs, config=config)
        self.is_loss = True

    def setup_defaults(self):
        super(L1RegularizationLoss, self).setup_defaults()
        self.conf_default("loss_weight", 0.001)

    def alloc(self):
        self.output_shape = (1,)

    def forward(self):
        if len(self.inputs) != 2:
            raise AssertionError("This node needs exactly two inputs to calculate loss")
        if not (self.inputs[0].W is not None and self.inputs[1].W is not None):
            raise AssertionError("L1 Regularization needs two nodes with weights as preceeding nodes")
        self.expression = (
            abs(self.inputs[0].W).sum() + abs(self.inputs[1].W).sum()
        )


@register_node
class L2RegularizationLoss(Node):
    """
    L1 regularization node for adjacent fc layers
    """
    def __init__(self, graph, name, inputs=[],config={}):
        """
        Constructor
        :param graph: Graph
        :param name: String
        :param config: Dict
        :return: Node
        """
        super(L2RegularizationLoss, self).__init__(graph, name, inputs=inputs, config=config)
        self.is_loss = True

    def setup_defaults(self):
        super(L2RegularizationLoss, self).setup_defaults()
        self.conf_default("loss_weight", 0.0001)

    def alloc(self):
        self.output_shape = (1,)

    def forward(self):
        if len(self.inputs) != 2:
            raise AssertionError("This node needs exactly two inputs to calculate loss")
        if not (self.inputs[0].W is not None and self.inputs[1].W is not None):
            raise AssertionError("L2 Regularization needs two nodes with weights as preceeding nodes")
        self.expression = (
            (self.inputs[0].W ** 2).sum() + (self.inputs[1].W ** 2).sum()
        )


@register_node
class LogarithmicScaleInvariantLoss(Node):
    """
    Compute log scale invariant error for depth prediction
    """
    def __init__(self, graph, name, inputs=[], config={}):
        """
        Constructor
        :param graph: Graph
        :param name: String
        :param config: Dict
        :return: Node
        """
        super(LogarithmicScaleInvariantLoss, self).__init__(graph, name, inputs=inputs,config=config)
        self.is_loss = True

    def setup_defaults(self):
        super(LogarithmicScaleInvariantLoss, self).setup_defaults()
        self.conf_default("loss_weight", 1.0)
        self.conf_default("lambda", 0.5)

    def alloc(self):
            self.output_shape = (1,)

    def forward(self):
            if len(self.inputs) != 2:
                raise AssertionError("This node needs exactly two inputs to calculate loss.")
            # Define our forward function
            in_0 = self.inputs[0].expression
            in_1 = self.inputs[1].expression
            EPS = 0.00001
            MAX = 1000000
            diff = T.log(T.clip(in_0, EPS, MAX)) - T.log(T.clip(in_1, EPS, MAX))
            self.expression = T.mean(diff**2) - ((self.conf("lambda") / (in_0.shape.prod()**2)) * (T.sum(diff)**2))


@register_node
class EuclideanLoss(Node):
    """
    Computes the loss according to the mean euclidean distance of the input tensors
    Equivalent to mean squared error (MSE)
    """
    def __init__(self, graph, name, inputs=[], config={}):
            """
            Constructor
            :param graph:  Graph
            :param name: String
            :param config: Dict
            :return:
            """
            super(EuclideanLoss, self).__init__(graph, name, inputs=inputs, config=config)
            self.is_loss = True

    def setup_defaults(self):
        super(EuclideanLoss, self).setup_defaults()
        self.conf_default("loss_weight", 1.0)

    def alloc(self):
        if len(self.inputs) != 2:
            raise AssertionError("This node needs exactly two inputs to calculate loss.")
        in_0 = self.inputs[0].output_shape
        in_1 = self.inputs[1].output_shape
        if in_0 != in_1:
            raise AssertionError("Input shapes have to be equal.")
        self.output_shape = (1,)

    def forward(self):
        # Define our forward function
        in_0 = self.inputs[0].expression
        in_1 = self.inputs[1].expression

        self.expression = T.mean((in_0 - in_1) ** 2)