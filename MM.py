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
from shared import Side, OType, TType
from math import floor

class MarketMaker():
    
    trader_type = TType.MarketMaker
    
    def __init__(self, mm_id, omega, gamma, kap, a, r, n, s, d, l, c):
        self.name = mm_id
        """initial MM capital"""
        self.kapital = kap
        """percent of capital allowed at risk"""
        self.max_kap_at_risk = omega
        """MM price sensitivity to realized volatility"""
        self.gamma = gamma
        """Initial MM inventory limit"""
        self.inv_limit = 0.5 * self.kapital
        """Starting inventory held, norm dist around 0"""
        self.inv = [random.normalvariate(mu=0, sigma=0.01) * self.inv_limit for _ in range(10)]
        self.inv = list(map(int, self.inv))
        """Decay strength of MM price signal"""
        self.alpha = a
        """Reduction for adverse selection"""
        self.r = r
        """Number of orders posted each side of orderbook"""
        self.n = n
        """Minimum bound on inferring demand signal"""
        self.s = s
        """Minimum bound on bid-ask spread"""
        self.delta = d
        """Time over which to consider realized price changes"""
        self.l = l
        """Sensitivity of private mid price to changes in inventory"""
        self.c = c
        """Risk associated with MM inventory held"""
        self.risk = [self.gamma * (self.inv[-1] / self.inv_limit)]
        """local order book for tracking own orders"""
        self.local_book = {}
        """Initial adjustment for inventory"""
        self.i = [0]
        """Minimum bid ask spread distance from personal mid price"""
        self.zeta = 0.01
        
        self._quote_sequence = 0
    
    """
*******************************************************************************
*******************************************************************************
    
    Figure out limit order quantities
    """
    
    def getQ(self):
        k = self.kapital
        omega = self.max_kap_at_risk
        return omega * k
    
    
    """This adjustment is used inside the method to determine bid and ask sizes"""
    def adjust_for_inv(self, side):
        max_inv = self.kapital * 0.5
        curr_inv = self.inv[-1]
        
        if side == Side.BID:
            adjustment = (curr_inv - max_inv) / max_inv
            return adjustment
        else:
            adjustment = (curr_inv + max_inv) / max_inv
            return adjustment
    
    
    """Determine reduction to take adverse selection into account"""
    def reduce_for_adv_sel(self, price1, pricel):
        p1 = price1
        pl = pricel
        reduction = self.r * abs(1 - (p1 / pl))
        return max([reduction, 1])
    
    
    """Get bid and ask sizes
    price1 = price last period
    pricel = price self.l periods ago"""
    def get_ab_q(self, price1, pricel):
        total_q = self.getQ()
        reduction = self.reduce_for_adv_sel(price1, pricel)
        bid_adj = self.adjust_for_inv(Side.BID)
        ask_adj = self.adjust_for_inv(Side.ASK)
        q_bid = ((0.5 * total_q) * (1/ self.n) * bid_adj * reduction)
        q_bid = abs(q_bid)
        q_ask = ((0.5 * total_q) * (1/ self.n) * ask_adj * reduction)
        return floor(q_ask), floor(q_bid)
    
    """    
*******************************************************************************
*******************************************************************************
    
    Figure out private mid point price
    """    
    
    """MM market-wide demand observation
    This is the estimate of demand that the market maker infers based
    on the balance of market orders at the current time period"""
    def demand_t(self, t, orders):
        if t == 1:
            d = 1
            return self.market.mw_demand[-t]
        if t > 1:
            d = (self.alpha * self.market.mw_demand[-t] + (1 - self.alpha) * self.demand[-t - 1])
            self.demand.append(d)
            return d
        
    
    """Determine if inventory changed from the last time I entered an order"""    
    def inventory_changed(self):
        if self.inv[-1] != self.inv[-2]:
            return True
        else:
            return False
    
    
    """Determine risk associated with current inventory"""
    def indicator(self):
        if self.inventory_changed():
            c = self.c
            inv_ratio_to_max = self.inv[-1] / self.inv_limit
            inv_risk = c * inv_ratio_to_max
            self.risk.append(inv_risk)
            return inv_risk
        else:
            inv_risk = self.risk[-1]
            return inv_risk
    
    
    def price_impact_buy(self, demand):
        if demand > self.s:
            return demand
        else:
            return 0
        
    
    def price_impact_sell(self, demand):
        if demand < -self.s:
            return demand
        else:
            return 0
    
    
    """Determine desired mid price based on market mid price
    observed price impact from market orders and inventory risk"""
    def set_mm_mid_price(self, signal):
        mp = signal.mid_price[-1]
        demand = signal.demand[-1]
        i = self.indicator()
        self.i.append(i)
        pib = self.price_impact_buy(demand)
        pia = self.price_impact_sell(demand)
        #personal_mp = mp + pib + pia + i
        personal_mp = mp - i
        return personal_mp


    """    
*******************************************************************************
*******************************************************************************
    
    Figure out bid ask spread
    """
    
    def set_spread(self, signal, demand):
        pmp = self.set_mm_mid_price(signal)
        """market wide mid price volatility in last 10 periods"""
        signal.calculate_volatility()
        volatility = signal.volatility
        min_ask = round(pmp + max([self.gamma * volatility, self.zeta]) + (self.i[-1] * (10**-10)), 2)
        max_bid = round(pmp - max([self.gamma * volatility, self.zeta]) - (self.i[-1] * (10**-10)), 2)
        
        if min_ask <= signal.tob["best_bid"]:
            min_ask = signal.tob["best_bid"] + (self.zeta)
        if max_bid >= signal.tob["best_ask"]:
            max_bid = signal.tob["best_ask"] - (self.zeta)
        
        return round(min_ask, 2), round(max_bid, 2)
    


    """    
*******************************************************************************
*******************************************************************************
    
    Process signal
    """
    
    def _make_add_quote(self, time, side, price, size):
        '''Make one add quote (dict)'''
        self._quote_sequence += 1
        return {'order_id': self._quote_sequence, 'trader_id': self.name, 
                'timestamp': time, 'type': OType.ADD, 'quantity': size, 
                'side': side, 'price': price}
        

    def process_signal(self, time, signal):
        if time > 100:
            x = time
        demand = signal.demand[-1]
        price1 = signal.mid_price[-1]
        pricel = signal.mid_price[-self.l]
        best_ask, best_bid = signal.report_ask_bid()
        my_ask, my_bid = self.set_spread(signal, demand)
        q_ask, q_bid = self.get_ab_q(price1, pricel)
        quote_list = []
        for n in range(self.n):
            quote_list.append(self._make_add_quote(time, Side.ASK, my_ask, abs(q_ask)))
            quote_list.append(self._make_add_quote(time, Side.BID, my_bid, abs(q_bid)))
            my_ask += 0.01
            my_ask = round(my_ask, 2)
            my_bid -= 0.01
            my_bid = round(my_bid, 2)
        return quote_list
    




    def confirm_trade_local(self, confirm):
        previous_inv = self.inv[-1]
        if confirm["side"] == Side.ASK:
            self.inv.append(previous_inv - confirm["quantity"])
        else:
            self.inv.append(previous_inv + confirm["quantity"])
            

        
        
        

        
        

    
    
        
        