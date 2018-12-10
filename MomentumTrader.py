#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 14:08:28 2018

@author: charlie
"""

"""Momentum Trader"""

import random
from shared import Side, OType, TType

class MomentumTrader():
    
    trader_type = TType.MomentumTrader
    
    def __init__(self, mt_id, omega, inv_limit, time_window, h):
        self.name = mt_id
        self.omega = omega
        self.inv_limit = inv_limit
        self.inv = random.randint(0, self.inv_limit)
        self.l = time_window
        self.h = h
        self._quote_sequence = 0
    
    
    
    def _make_add_quote(self, time, side, price, size):
        '''Make one add quote (dict)'''
        self._quote_sequence += 1
        return {'order_id': self._quote_sequence, 'trader_id': self.name, 
                'timestamp': time, 'type': OType.ADD, 'quantity': size, 
                'side': side, 'price': price}

    
    
    
    def set_demand(self, signal):
        reduction = 1 - (self.inv / self.inv_limit)**self.h
        change = (signal.market_price[-1] - signal.market_price[-self.l]) / signal.market_price[-self.l]
        d = self.omega * change * reduction
        return d
    
    
    def process_signal(self, time, signal):
        size, buy_sell = self.set_demand(signal)
        return self._make_add_quote(time, buy_sell, 200000, size)
        