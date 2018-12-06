#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 14:08:28 2018

@author: charlie
"""

"""Momentum Trader"""

import random

class MomentumTrader():
    
    def __init__(self, **kwargs):
        self.Lambda = kwargs["pmt"]
        self.omega = kwargs["mom_omega"]
        self.h = kwargs["mom_shape"]
        self.inv_limit = kwargs["mom_inv_limit"]
        self.inv = random.randint(0, self.inv_limit)
        self.l = kwargs["mom_time_window"]
    
    
    
    def can_i_trade(self):
        if random.random() < self.Lambda:
            return 1
        else:
            return 0
    
    
    def get_price_change(self):
        p = self.exchange.price_hist[-1]
        pl = self.exchange.price_hist[-self.l]
        change = (p - pl) / pl
        return change
    
    
    
    def set_demand(self):
        if self.can_i_trade() == 1:
            reduction = 1 - (self.inv / self.inv_limit)**self.h
            change = self.get_price_change()
            d = self.omega * change * reduction
            return d
        else:
            return 0
        