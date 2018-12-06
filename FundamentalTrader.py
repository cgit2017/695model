#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 13:42:30 2018

@author: charlie
"""

"""Fundamental Trader"""

import random


class FundamentalTrader():
    
    def __init__(self, f, omega, sigma, exchange):
        self.sigma = sigma
        self.value = 100
        self.omega = omega
        self.exchange = exchange
    
    
    
    def set_fund_value(self):
        self.value += random.normalvariate(mu=0, sigma=self.sigma)
    
    
    
    def set_demand(self, signal):
        self.set_fund_value()
        ask = signal["best_ask"]
        bid = signal["best_bid"]
        Lambda = self.can_i_trade()
        if Lambda == 1:
            if bid < self.value < ask:
                return 0
            if self.value > ask:
                return Lambda * (self.omega * (self.value - ask))
            if self.value < bid:
                return Lambda * (self.omega * (self.value - bid))
        