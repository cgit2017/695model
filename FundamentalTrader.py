#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 13:42:30 2018

@author: charlie
"""

"""Fundamental Trader"""

import random
from shared import Side, OType, TType
from math import floor


class FundamentalTrader():
    
    trader_type = TType.FundamentalTrader
    
    def __init__(self, f, omega, sigma):
        self.name = f
        self.omega = omega
        self.sigma = sigma
        self.value = 50
        self._quote_sequence = 0
        
    
    
    
    def set_value(self):
        self.value += random.normalvariate(mu=0, sigma=self.sigma)
        
        
    def _make_add_quote(self, time, side, price, size):
        if size == 0 or side == 0:
            return None
        else:
            '''Make one add quote (dict)'''
            self._quote_sequence += 1
            return {'order_id': self._quote_sequence, 'trader_id': self.name, 
                    'timestamp': time, 'type': OType.ADD, 'quantity': size, 
                    'side': side, 'price': price}
    
    
    
    def set_demand(self, signal):
        self.set_value()
        ask = signal.ask
        bid = signal.bid
        if bid <= self.value <= ask: # value is between bid and ask
            return 0, 0
        elif self.value > ask: # value is above current market value, so buy
            d = self.omega * (self.value - ask)
            side = Side.BID
            return floor(d), side
        else: # value is below current market value, so sell
            d = self.omega * (self.value - bid)
            side = Side.ASK
            d = floor(abs(d)), side
            d = -1 * d
            return d, side
            
    
    
    def process_signal(self, time, signal):
        size, side = self.set_demand(signal)
        if side == Side.BID:
            return self._make_add_quote(time, side, 200000, size)
        else:
            return self._make_add_quote(time, side, 0, size)
        