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
    
    def __init__(self, market, **kwargs):
        """Probability that MM will enter market"""
        self.Lambda = kwargs["pmm"]
        """initial MM capital"""
        self.kapital = kwargs["kapital"]
        self.position = 0
        """percent of capital allowed at risk"""
        self.max_kap_at_risk = kwargs["kap_at_risk"]
        """MM price sensitivity to realized volatility"""
        self.gamma = kwargs["gamma"]
        """Initial MM inventory limit"""
        self.inv_limit = 0.5 * self.kapital
        """Starting inventory held, norm dist around 0"""
        self.inv = [random.normalvariate(mu=0, sigma=0.01) * self.inv_limit]
        """Decay strength of MM price signal"""
        self.alpha = kwargs["alpha"]
        """Reduction for adverse selection"""
        self.r = kwargs["reduction"]
        """Number of orders posted each side of orderbook"""
        self.n = kwargs["n_orders"]
        """Minimum bound on inferring demand signal"""
        self.s = kwargs["min_sig"]
        """Minimum bound on bid-ask spread"""
        self.delta = kwargs["min_spread"]
        """Time over which to consider realized price changes"""
        self.l = kwargs["time_window"]
        """The overall market environment the MM exists in, which includes
        the two exchanges"""
        self.market = market
        """Past observed demand"""
        self.demand = []
        """Risk associated with MM inventory held"""
        self.risk = [self.gamma * (self.inv / self.inv_limit)]
    
    
    """Figure out if MM will trade this period"""
    def can_i_trade(self):
        if random.random() < self.Lambda:
            return 1
        else:
            return 0
    
    
    def getQ(self):
        k = self.kapital
        omega = self.max_kap_at_risk
        return omega * k
    
    
    def adjust_for_inv(self, ab):
        max_inv = self.kapital * 0.5
        curr_inv = self.inv
        if ab == "bid":
            return (curr_inv - max_inv) / max_inv
        else:
            return (curr_inv + max_inv) / max_inv
    
    
    def reduce_for_adv_sel(self, price1, pricel):
        p1 = price1
        pl = pricel
        return self.r * (1 - abs(p1 / pl))
    
    
    """Get bid and ask quantities"""
    def get_ab_q(self, price1, pricel):
        Lambda = self.can_i_trade()
        total_q = self.getQ()
        reduction = self.reduce_for_adv_sel(price1, pricel)
        q_bid = (Lambda * (0.5 * total_q) * (1/ self.n) * self.adjust_for_inv("bid") * reduction)
        q_ask = (Lambda * (0.5 * total_q) * (1/ self.n) * self.adjust_for_inv("ask") * reduction)
        return q_ask, q_bid
    
    
    """MM market-wide demand observation
    This is the estimate of demand that the market maker infers based
    on the balance of market orders at the current time period"""
    def demand_t(self, t):
        if t == 1:
            self.demand.append(self.market.mw_damand[-t])
            return self.market.mw_demand[-t]
        if t > 1:
            d = (self.alpha * self.market.mw_demand[-t] + (1 - self.alpha) * self.demand[-t - 1])
            self.demand.append(d)
            return d
        
    
    """Determine if inventory changed from the last time I entered an order"""    
    def inventory_changed(self):
        inv_change = abs(self.inv[-1] - self.inv[-2])
        if inv_change > 0:
            return True
        if inv_change == 0:
            return False
    
    
    """Determine risk associated with current inventory"""
    def indicator(self):
        if self.inventory_changed():
            c = self.gamma
            inv_ratio_to_max = self.inv[-1] / self.inv_limit
            inv_risk = c * inv_ratio_to_max
            self.risk.append(inv_risk)
            return inv_risk
        else:
            inv_risk = self.risk[-1]
            return inv_risk
    
    
    """Determine desired mid price based on market mid price
    observed price impact from market orders and inventory risk"""
    def set_mm_mid_price(self):
        mp = self.market.mid_price()
    
    
    def process_signal(self, signal):
        
        
        
        
"""Keyword Args for MM
pmm, kapital, kap_at_risk, gamma, alpha, reduction, n_orders, min_sig, min_spread, time_window
"""
    
    
        
        