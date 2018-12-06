#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 13:33:59 2018

@author: charlie
"""

"""Noise Trader"""

"""
Posts market orders randomly (random size and direction)
Market order size is normally distributed
"""

import random

class NoiseTrader():
    
    def __init__(self, n, sigma):
        self.trader_id = n
        self.sigma = sigma
        self.demand_hist = []
    
    
    
    def set_demand(self):
        noise = random.normalvariate(mu=0, sigma=self.sigma)
        if random.random() > 0.5:
            buy_sell = 1
        else:
            buy_sell = -1
        return noise, buy_sell