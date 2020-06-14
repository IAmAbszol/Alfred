import numpy as np

from hmmlearn import hmm
from sklearn.utils import check_random_state
'''
X1 = [[0.5], [1.0], [-1.0], [0.42], [0.24]]
X2 = [[2.4], [4.2], [0.5], [-0.24]]

X = np.concatenate([X1, X2])
lengths = [len(X1), len(X2)]
'''

X = [[i] for i in range(5)] * 10000
lengths = [len(X)]
model = hmm.GaussianHMM(n_components=5, covariance_type='full', n_iter=100).fit(X)

for pred in [0,1,2,3,4]:
    state = model.predict([[pred]])
    prob_next_step = model.transmat_[state[-1], :]
    print(prob_next_step)