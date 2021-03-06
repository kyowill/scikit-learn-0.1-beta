# req'd file for SciPy package (see DEVELOPERS.txt)
# Fred Mailhot
# 2006-06-13

"""
An artificial neural network module for scipy, adding standard feedforward architectures
(MLP and RBF), as well as some recurrent architectures (e.g. SRN).

Each of {mlp,srn,rbf}.py contains a class to define, train and test a network,
along with a main() functions that demos on a toy dataset.
"""

__all__ = ['mlp','srn','rbf']

