import random
import time

import numpy as np
import pandas as pd

import orderbook as orderbook
from shared import Side, OType, TType


from MM import MarketMaker
from NoiseTrader import NoiseTrader
from FundamentalTrader import FundamentalTrader
from MomentumTrader import MomentumTrader
from Signal import Signal

class Runner:
    
    def __init__(self, h5filename='test.h5', prime1=20, run_steps=10000, write_interval=5000, **kwargs):
        self.signal = Signal()
        self.exchange = orderbook.Orderbook(self.signal)
        self.h5filename = h5filename
        self.run_steps = run_steps + 1
        self.liquidity_providers = {}
        self.noise = kwargs.pop('Noise')
        # Set up noise traders
        if self.noise:
            self.noise_traders = self.buildNoiseTraders(kwargs['numNoise'], 
                                                        kwargs["NoiseSigma"])
            self.Lambda_nt = kwargs['Lambda_nt']
        # Set up fundamental traders    
        self.fundamental = kwargs.pop("Fundamental")
        if self.fundamental:
            self.fundamentals = self.buildFundamentalTraders(kwargs['numFund'], 
                                                             kwargs["omega_Fund"], 
                                                             kwargs["FundSigma"])
            self.Lambda_ft = kwargs["Lambda_ft"]
        # Set up momentum traders
        self.momentum = kwargs.pop("Momentum")
        if self.momentum:
            self.momentums = self.buildMomentumTraders(kwargs["numMom"], 
                                                       kwargs["omega_Mom"],
                                                       kwargs["MomInvLim"],
                                                       kwargs["MomTimeWindow"],
                                                       kwargs["shapeMom"])
            self.Lambda_mt = kwargs["Lambda_mt"]
        # Set up Market Makers    
        self.marketmaker = kwargs.pop("MarketMaker")
        if self.marketmaker:
            self.marketmakers = self.buildMarketMakers(kwargs["numMMs"], 
                                                       kwargs["KatRisk"], 
                                                       kwargs["MMgamma"],
                                                       kwargs["K"],
                                                       kwargs["MMa"],
                                                       kwargs["MMr"],
                                                       kwargs["MMn"],
                                                       kwargs["MMs"],
                                                       kwargs["MMdelta"],
                                                       kwargs["MMwindow"],
                                                       kwargs["MMc"])
            self.Lambda_mm = kwargs["Lambda_mm"]
        
        
        self.traders, self.num_traders = self.makeAll()
        self.seedOrderbook()
#        if self.provider:
#            self.makeSetup(prime1, kwargs['Lambda0'])
#        if self.pj:
#            self.runMcsPJ(prime1, write_interval)
#        else:
        self.runMcs(prime1, write_interval)
        self.exchange.trade_book_to_h5(h5filename)
        self.qTakeToh5()
        self.mmProfitabilityToh5()
        
        
                  
    def buildNoiseTraders(self, numNoise, NoiseSigma):
        ''' Noise trader id starts with 1'''
        noise_ids = [1000 + i for i in range(numNoise)]
        noise_list = [NoiseTrader(n, NoiseSigma) for n in noise_ids]
        #self.liquidity_providers.update(dict(zip(noise_ids, noise_list)))
        return noise_list
    
    def buildFundamentalTraders(self, numFunds, omega, sigma):
        ''' Fundamental id starts with 2'''
        fundamentals_ids = [2000 + i for i in range(numFunds)]
        return [FundamentalTrader(f, omega, sigma) for f in fundamentals_ids]
    
    def buildMomentumTraders(self, numMoms, omega, inv_limit, time_window, h):
        ''' Momentum trader id starts with 5'''
        momentum_ids = [5000 + i for i in range(numMoms)]
        return [MomentumTrader(mt, omega, inv_limit, time_window, h) for mt in momentum_ids]
    
    def buildMarketMakers(self, numMMs, KatRisk, gamma, K, alpha, reduction, n, s, delta, window, c):
        ''' MM id starts with 4'''
        mm_ids = [4000 + i for i in range(numMMs)]
        #self.liquidity_providers.update({4000: jumper})
        return [MarketMaker(mm_id=mm, omega=KatRisk, gamma=gamma, kap=K, a=alpha, r=reduction,
                            n=n, s=s, d=delta, l=window, c=0.03) for mm in mm_ids]

    
    def makeAll(self):
        trader_list = []
        if self.noise:
            trader_list.extend(self.noise_traders)
        if self.fundamental:
            trader_list.extend(self.fundamentals)
        if self.momentum:
            trader_list.extend(self.momentums)
        if self.marketmaker:
            trader_list.extend(self.marketmakers)
        return trader_list, len(trader_list)


    
    def seedOrderbook(self):
        seed_mm = MarketMaker(9999, 1, 0.05, 10000, 0.15, 1000, 4, 0.00001, 0.0001, 10, 0.03)
        self.liquidity_providers.update({9999: seed_mm})
        for _ in range(100):
            ba = round(random.uniform(50., 50.1), 2)
            bb = round(random.uniform(49.9, 49.99), 2)
            qask = {'order_id': 0, 'trader_id': 9999, 'timestamp': 0, 'type': OType.ADD, 
                    'quantity': 1, 'side': Side.ASK, 'price': ba}
            qbid = {'order_id': 0, 'trader_id': 9999, 'timestamp': 0, 'type': OType.ADD,
                    'quantity': 1, 'side': Side.BID, 'price': bb}
            seed_mm.local_book[1] = qask
            self.exchange.add_order_to_book(qask)
            self.exchange.add_order_to_history(qask)
            seed_mm.local_book[2] = qbid
            self.exchange.add_order_to_book(qbid)
            self.exchange.add_order_to_history(qbid)
            self.signal.calculate_mid_price(self.exchange.report_top_of_book(0))
        
#    def makeSetup(self, prime1, lambda0):
#        top_of_book = self.exchange.report_top_of_book(0)
#        for current_time in range(1, prime1):
#            ps = random.sample(self.providers, self.num_providers)
#            for p in ps:
#                if not current_time % p.delta_t:
#                    self.exchange.process_order(p.process_signal(current_time, top_of_book, self.q_provide, -lambda0))
#                    top_of_book = self.exchange.report_top_of_book(current_time)    
#    
#    def doCancels(self, trader):
#        for c in trader.cancel_collector:
#            self.exchange.process_order(c)
                    
    def confirmTrades(self):
        for c in self.exchange.confirm_trade_collector:
            contra_side = self.liquidity_providers[c['trader']]
            contra_side.confirm_trade_local(c)
    
    def runMcs(self, prime1, write_interval):
        top_of_book = self.exchange.report_top_of_book(1)
        traders = self.traders
        for current_time in range(1, self.run_steps):
            self.signal.demand_updated = False
            for t in traders:
                if t.trader_type == TType.NoiseTrader:
                    if random.random() <= self.Lambda_nt:
                        order = t.process_signal(current_time)
                        self.exchange.process_order(order)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                        self.signal.calculate_mid_price(top_of_book)
                        self.signal.calculate_volatility()
                        if self.signal.demand_updated:
                            self.signal.demand[-1] += order["quantity"]
                        else:
                            self.signal.demand.append(order["quantity"])
                            self.signal.demand_updated = True
#                    t.bulk_cancel(current_time)
#                    if t.cancel_collector:
#                        self.doCancels(t)
#                        top_of_book = self.exchange.report_top_of_book(current_time)
                elif t.trader_type == TType.FundamentalTrader:
                    if random.random() <= self.Lambda_ft:
                        order = t.process_signal(current_time, self.signal)
                        if order is None:
                            pass
                        else:
                            self.exchange.process_order(order)
                            top_of_book = self.exchange.report_top_of_book(current_time)
                            self.signal.calculate_mid_price(top_of_book)
                            self.signal.calculate_volatility()
                            if self.signal.demand_updated:
                                self.signal.demand[-1] += order["quantity"]
                            else:
                                self.signal.demand.append(order["quantity"])
                                self.signal.demand_updated = True
#                    t.bulk_cancel(current_time)
#                    if t.cancel_collector:
#                        self.doCancels(t)
#                        top_of_book = self.exchange.report_top_of_book(current_time)
                elif t.trader_type == TType.MomentumTrader:
                    if random.random() <= self.Lambda_mt:
                        order = t.process_signal(current_time, self.signal)
                        self.exchange.process_order(order)
                        if self.exchange.traded:
                            self.confirmTrades()
                            top_of_book = self.exchange.report_top_of_book(current_time)
                            self.signal.calculate_mid_price(top_of_book)
                            self.signal.calculate_volatility()
                            if self.signal.demand_updated:
                                self.signal.demand[-1] += order["quantity"]
                            else:
                                self.signal.demand.append(order["quantity"])
                else: # Trader is Market Maker
                    if random.random() <= self.Lambda_mm:
                        quotes = t.process_signal(current_time, self.signal)
                        for q in quotes:
                            self.exchange.process_order(q)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                        if self.exchange.traded:
                            self.confirmTrades()
                            top_of_book = self.exchange.report_top_of_book(current_time)
                            self.signal.calculate_mid_price(top_of_book)
                            self.signal.calculate_volatility()
            if not current_time % write_interval:
                self.exchange.order_history_to_h5(self.h5filename)
                self.exchange.sip_to_h5(self.h5filename)
                
    
                
    def qTakeToh5(self):
        temp_df = pd.DataFrame({'qt_take': self.q_take, 'lambda_t': self.lambda_t})
        temp_df.to_hdf(self.h5filename, 'qtl', append=True, format='table', complevel=5, complib='blosc')
        
    def mmProfitabilityToh5(self):
        for m in self.marketmakers:
            temp_df = pd.DataFrame(m.cash_flow_collector)
            temp_df.to_hdf(self.h5filename, 'mmp', append=True, format='table', complevel=5, complib='blosc')
    
    
if __name__ == '__main__':
    
    print(time.time())
    
    settings = {"Noise": True, "numNoise": 1, "NoiseSigma": 50, "Lambda_nt": 0.02,
                "Fundamental": True, "numFund": 1, "omega_Fund": 500, "FundSigma": 0.0000156, "Lambda_ft": 0.1,
                "Momentum": True, "numMom": 1, "omega_Mom": 50000, "MomInvLim": 300, "MomTimeWindow": 10, "shapeMom": 4, "Lambda_mt": 0.2,
                "MarketMaker": True, "numMMs": 1, "KatRisk": 0.12, "MMgamma": 3, 
                "K": 10000, "MMa": 0.15, "MMr": 1000, "MMn": 4, "MMs": 0.00001, 
                "MMdelta": 0.0001, "MMwindow": 10, "Lambda_mm": 0.2, "MMc": 0.01
                }
    
    r = Runner(**settings)
    
#    for j in range(51, 52):
#        random.seed(j)
#        np.random.seed(j)
#    
#        start = time.time()
#        
#        h5_root = 'python_pyziabmc_tdelta_%d' % j
#        h5dir = 'C:\\Users\\user\\Documents\\Agent-Based Models\\h5 files\\Trial 901\\'
#        h5_file = '%s%s.h5' % (h5dir, h5_root)
#    
#        market1 = Runner(h5filename=h5_file, **settings)
#
#        print('Run %d: %.1f seconds' % (j, time.time() - start))