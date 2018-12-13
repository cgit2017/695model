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
from shared import Side, OType, TType
from math import floor

class NoiseTrader():
    
    trader_type = TType.NoiseTrader
    
    def __init__(self, n, sigma):
        self.name = n
        self.sigma = sigma
        self.demand_hist = []
        self._quote_sequence = 0
        self.quote_collector = []
    
    
    def _make_add_quote(self, time, side, price, size):
        '''Make one add quote (dict)'''
        self._quote_sequence += 1
        return {'order_id': self._quote_sequence, 'trader_id': self.name, 
                'timestamp': time, 'type': OType.ADD, 'quantity': size, 
                'side': side, 'price': price}
    
    
    def set_demand(self):
        size = random.normalvariate(mu=0, sigma=self.sigma)
        if random.random() > 0.5:
            buy_sell = Side.BID
            size = floor(size)
        else:
            buy_sell = Side.ASK
            size = floor(abs(size))
        return size, buy_sell
    
    
    def process_signal(self, time):
        size, buy_sell = self.set_demand()
        if buy_sell == Side.BID:
            return self._make_add_quote(time, buy_sell, 200000, abs(size))
        else:
            return self._make_add_quote(time, buy_sell, 0, abs(size))
        