#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Python version: 3.6

import copy
import torch
import numpy as np
import random
from torch import nn

def numpy_to_state_dict(w: np.array, structure: "dict[str, torch.Tensor]"):
    ww = {}
    start, end = 0, 0
    for k in structure[0].keys():
        end += torch.numel(structure[0][k])
        ww[k] = torch.from_numpy(np.reshape(w[start:end], structure[0][k].size()))
        start = end
    return ww


def state_dict_to_numpy(w: "dict[str, torch.Tensor]"):
    grads = np.zeros(0)
    for k in w.keys():
        grads = np.concatenate((grads, w[k].data.numpy().flatten()), axis=None)
    return grads


def locals_to_numpy(w: "list[dict[str,torch.Tensor]]"):
    w_c = copy.deepcopy(w)
    ww = np.zeros(0)
    for i in range(num_of_veh := len(w_c)):
        grads = state_dict_to_numpy(w_c[i])
        ww = np.concatenate((ww, grads))
    ww = np.reshape(ww, (num_of_veh, int(len(ww)/num_of_veh)))
    return ww

def model_sub(w1, w2):
    counter = 0
    w_diff = copy.deepcopy(w1)
    
    for k in w1.keys():
        for i in range(1, len(w1)):
            try:
                w_diff[k] = torch.sub(w1[k], w2[k])
            except Exception as e: 
                # not dtype
                counter += 1
                pass

    return w_diff

def model_add(w1, w2):
    counter = 0
    w_diff = copy.deepcopy(w1)
    
    for k in w1.keys():
        for i in range(1, len(w1)):
            try:
                w_diff[k] = torch.add(w1[k], w2[k])
            except Exception as e: 
                # not dtype
                counter += 1
                pass

    return w_diff
