import torch
import torch.jit

from .flatten import Flatten
from ..ir import Tensor, Node

__all__ = ['trace']


def trace(model, *args, **kwargs):
    assert not kwargs, 'keyword argument is not supported for now. use positional arguments instead!'
    trace, _ = torch.jit.get_trace_graph(Flatten(model), tuple(args), kwargs=kwargs)

    tensors = dict()
    for node in trace.graph().nodes():
        for var in list(node.inputs()) + list(node.outputs()):
            if 'tensor' in var.type().kind().lower():
                dtype = var.type().scalarType()
                shape = var.type().sizes()
            else:
                dtype = str(var.type())
                shape = None
            tensors[var] = Tensor(name=var.debugName(), dtype=dtype, shape=shape)

    nodes = []
    for node in trace.graph().nodes():
        inputs = [tensors[var] for var in node.inputs()]
        outputs = [tensors[var] for var in node.outputs()]
        attributes = {name: getattr(node, node.kindOf(name))(name) for name in node.attributeNames()}
        nodes.append(Node(operator=node.kind(), attributes=attributes, inputs=inputs, outputs=outputs,
                          scope=node.scopeName().replace('Flatten/', '')))
    return nodes