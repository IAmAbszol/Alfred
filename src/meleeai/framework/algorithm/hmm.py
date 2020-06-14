#!/usr/bin/env python
from hmmlearn import hmm

class HiddenMarkovModel(object):
    """Class that controls the main part of the AI"""

    def __init__(self, pretrained_model=None):
        self.model = pretrained_model

    def train(self, data, n_components=1, covariance_type='full', n_iter=100, verbose=False):
        # Train on parameters passed through including data
        """
            The data coming in should be able to be translated properly into a sequence of actions
            and possibly assign meaningful values to them.
            there should also be considered combo button inputs per pre/post. Consider this.

            Such as, there should also be a release/neutral state on control sticks.
            
        """

    def predict(self):
