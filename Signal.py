#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 13:11:13 2018

@author: charlie
"""

"""
Signal Class
"""

import numpy as np

class Signal():
    
    def __init__(self):
        self.demand_updated = False
        self.demand = [0]
        self.volatility = 0
        self.market_price = []
        self.ask = 0
        self.bid = 0
    
    
    def calculate_volatility(self):
        self.volatility = np.std(self.market_price[-10:])
        
    def calculate_mid_price(self, tob):
        self.ask = tob["best_ask"]
        self.bid = tob["best_bid"]
        mid_price = (self.ask + self.bid) / 2
        self.market_price.append(mid_price)