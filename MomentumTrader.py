#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 14:08:28 2018

@author: charlie
"""

"""Momentum Trader"""

import random
from shared import Side, OType, TType
from math import floor

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
        change = (signal.mid_price[-1] - signal.mid_price[-self.l]) / signal.mid_price[-self.l]
        d = self.omega * change * reduction
        if d < 0:
            side = Side.ASK
            d = floor(abs(d))
            d = -1 * d
        elif d > 0:
            side = Side.BID
            d = floor(d)
        else:
            side = None
        return d, side
    
    
    def process_signal(self, time, signal):
        size, buy_sell = self.set_demand(signal)
        if size == 0:
            return None
        if buy_sell == Side.BID:
            return self._make_add_quote(time, buy_sell, 200000, abs(size))
        else:
            return self._make_add_quote(time, buy_sell, 0, abs(size))
        