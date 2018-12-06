#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 18:07:13 2018

@author: charlie
"""

"""
Market Maker
"""

import random

class MarketMaker():
    
    def __init__(self, trade_freq, kapital, kap_at_risk, gamma, alpha, reduction, n_orders, min_sig, min_spread, time_window):
        """Probability that MM will enter market"""
        self.Lambda = trade_freq
        """initial MM capital"""
        self.kapital = kapital
        self.position = 0
        """percent of capital allowed at risk"""
        self.kap_at_risk = kap_at_risk
        """MM price sensitivity to realized volatility"""
        self.gamma = gamma
        """MM inventory limit"""
        self.inv_limit = 0.5 * self.kapital
        """Decay strength of MM price signal"""
        self.alpha = alpha
        """Reduction for adverse selection"""
        self.r = reduction
        """Number of orders posted each side of orderbook"""
        self.n = n_orders
        """Minimum bound on inferring demand signal"""
        self.s = min_sig
        """Minimum bound on bid-ask spread"""
        self.delta = min_spread
        """Time over which to consider realized price changes"""
        self.l = time_window
    
    
    def can_i_trade(self):
        if random.random() < self.Lambda:
            return 1
        else:
            return 0
    
    
    def getQ(self):
        k = self.kapital
        omega = self.kap_at_risk
        return omega * k
    
    
    def adjust_for_inv(self):
        max_inv = self.kapital * 0.5
        curr_inv = self.inv
        return (curr_inv - max_inv) / max_inv
    
    def reduce_for_adv_sel(self, price1, pricel):
        p1 = price1
        pl = pricel
        return self.r * (1 - abs(p1 / pl))
    
    """Get bid and ask quantities"""
    def get_ab_q(self, price1, pricel):
        q_bid = (self.can_i_trade() * (0.5 * self.getQ()) * (1/ self.n) * self.adjust_for_inv() * self.reduce_for_adv_sel(price1, pricel) )
        
        
    
    
        
        