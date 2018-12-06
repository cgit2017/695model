import random
import time

import numpy as np
import pandas as pd

import orderbook as orderbook
import trader as trader

from shared import Side, OType, TType

import MM, NoiseTrader, FundamentalTrader, MomentumTrader


class Runner:
    
    def __init__(self, h5filename='test.h5', mpi=1, prime1=20, run_steps=10000, write_interval=5000, **kwargs):
        self.exchange = orderbook.Orderbook()
        self.h5filename = h5filename
        self.mpi = mpi
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
                                                       kwargs["MomSigma"],
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
                                                       kwargs["MMwindow"])
            self.Lambda_mm = kwargs["Lambda_mm"]
        
        
        self.traders, self.num_traders = self.makeAll()
        self.seedOrderbook(kwargs['pAlpha'])
        if self.provider:
            self.makeSetup(prime1, kwargs['Lambda0'])
        if self.pj:
            self.runMcsPJ(prime1, write_interval)
        else:
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
    
    def buildMomentumTraders(self, numMoms, omega, sigma, inv_limit, time_window, h):
        ''' Momentum trader id starts with 5'''
        momentum_ids = [5000 + i for i in range(numMoms)]
        return [MomentumTrader(m, omega, sigma, inv_limit, time_window, h) for m in momentum_ids]
    
    def buildMarketMakers(self, numMMs, KatRisk, gamma, K, alpha, reduction, n, s, delta, window):
        ''' MM id starts with 4'''
        mm_ids = [4000 + i for i in range(numMMs)]
        #self.liquidity_providers.update({4000: jumper})
        return [MM(mm, KatRisk, gamma, K, alpha, reduction, n, s, delta, window) for mm in mm_ids]

    
    def makeAll(self):
        trader_list = []
        if self.noise:
            trader_list.extend(self.noise_traders)
        if self.fundamental:
            trader_list.extend(self.fundamentals)
        if self.momentum:
            trader_list.extend(self.momentums)
        if self.marketmaker:
            trader_list.append(self.marketmakers)
        return trader_list, len(trader_list)



"""
*******************************************************************
Start here
*******************************************************************
"""    
    def seedOrderbook(self, pAlpha):
        seed_provider = MM(9999, 1, 0.05, pAlpha)
        self.liquidity_providers.update({9999: seed_provider})
        ba = random.choice(range(1000005, 1002001, 5))
        bb = random.choice(range(997995, 999996, 5))
        qask = {'order_id': 1, 'trader_id': 9999, 'timestamp': 0, 'type': OType.ADD, 
                'quantity': 1, 'side': Side.ASK, 'price': ba}
        qbid = {'order_id': 2, 'trader_id': 9999, 'timestamp': 0, 'type': OType.ADD,
                'quantity': 1, 'side': Side.BID, 'price': bb}
        seed_provider.local_book[1] = qask
        self.exchange.add_order_to_book(qask)
        self.exchange.add_order_to_history(qask)
        seed_provider.local_book[2] = qbid
        self.exchange.add_order_to_book(qbid)
        self.exchange.add_order_to_history(qbid)
        
    def makeSetup(self, prime1, lambda0):
        top_of_book = self.exchange.report_top_of_book(0)
        for current_time in range(1, prime1):
            ps = random.sample(self.providers, self.num_providers)
            for p in ps:
                if not current_time % p.delta_t:
                    self.exchange.process_order(p.process_signal(current_time, top_of_book, self.q_provide, -lambda0))
                    top_of_book = self.exchange.report_top_of_book(current_time)    
    
    def doCancels(self, trader):
        for c in trader.cancel_collector:
            self.exchange.process_order(c)
                    
    def confirmTrades(self):
        for c in self.exchange.confirm_trade_collector:
            contra_side = self.liquidity_providers[c['trader']]
            contra_side.confirm_trade_local(c)
    
    def runMcs(self, prime1, write_interval):
        top_of_book = self.exchange.report_top_of_book(prime1)
        for current_time in range(prime1, self.run_steps):
            traders = random.sample(self.traders, self.num_traders)
            for t in traders:
                if t.trader_type == TType.Provider:
                    if not current_time % t.delta_t:
                        self.exchange.process_order(t.process_signal(current_time, top_of_book, self.q_provide, self.lambda_t[current_time]))
                        top_of_book = self.exchange.report_top_of_book(current_time)
                    t.bulk_cancel(current_time)
                    if t.cancel_collector:
                        self.doCancels(t)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                elif t.trader_type == TType.MarketMaker:
                    if not current_time % t.quantity:
                        t.process_signal(current_time, top_of_book, self.q_provide)
                        for q in t.quote_collector:
                            self.exchange.process_order(q)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                    t.bulk_cancel(current_time)
                    if t.cancel_collector:
                        self.doCancels(t)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                elif t.trader_type == TType.Taker:
                    if not current_time % t.delta_t:
                        self.exchange.process_order(t.process_signal(current_time, self.q_take[current_time]))
                        if self.exchange.traded:
                            self.confirmTrades()
                            top_of_book = self.exchange.report_top_of_book(current_time)
                else:
                    if current_time in t.delta_t:
                        self.exchange.process_order(t.process_signal(current_time))
                        if self.exchange.traded:
                            self.confirmTrades()
                            top_of_book = self.exchange.report_top_of_book(current_time)
            if not current_time % write_interval:
                self.exchange.order_history_to_h5(self.h5filename)
                self.exchange.sip_to_h5(self.h5filename)
                
    def runMcsPJ(self, prime1, write_interval):
        top_of_book = self.exchange.report_top_of_book(prime1)
        for current_time in range(prime1, self.run_steps):
            traders = random.sample(self.traders, self.num_traders)
            for t in traders:
                if t.trader_type == TType.Provider:
                    if not current_time % t.delta_t:
                        self.exchange.process_order(t.process_signal(current_time, top_of_book, self.q_provide, self.lambda_t[current_time]))
                        top_of_book = self.exchange.report_top_of_book(current_time)
                    t.bulk_cancel(current_time)
                    if t.cancel_collector:
                        self.doCancels(t)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                elif t.trader_type == TType.MarketMaker:
                    if not current_time % t.quantity:
                        t.process_signal(current_time, top_of_book, self.q_provide)
                        for q in t.quote_collector:
                            self.exchange.process_order(q)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                    t.bulk_cancel(current_time)
                    if t.cancel_collector:
                        self.doCancels(t)
                        top_of_book = self.exchange.report_top_of_book(current_time)
                elif t.trader_type == TType.Taker:
                    if not current_time % t.delta_t:
                        self.exchange.process_order(t.process_signal(current_time, self.q_take[current_time]))
                        if self.exchange.traded:
                            self.confirmTrades()
                            top_of_book = self.exchange.report_top_of_book(current_time)
                else:
                    if current_time in t.delta_t:
                        self.exchange.process_order(t.process_signal(current_time))
                        if self.exchange.traded:
                            self.confirmTrades()
                            top_of_book = self.exchange.report_top_of_book(current_time)
                if random.random() < self.alpha_pj:
                    self.pennyjumper.process_signal(current_time, top_of_book, self.q_take[current_time])
                    if self.pennyjumper.cancel_collector:
                        for c in self.pennyjumper.cancel_collector:
                            self.exchange.process_order(c)
                    if self.pennyjumper.quote_collector:
                        for q in self.pennyjumper.quote_collector:
                            self.exchange.process_order(q)
                    top_of_book = self.exchange.report_top_of_book(current_time)
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
                "Momentum": True, "numMom": 1, "omega_mom": 50000, "MomInvLim": 300, "MomTimeWindow": 10, "shapeMom": 4, "Lambda_mt": 0.2,
                "MarketMaker": True, "NumMMs": 1, "KatRisk": 0.12, "MMgamma": 3, 
                "K": 10000, "MMa": 0.15, "MMr": 1000, "MMn": 4, "MMs": 0.00001, 
                "MMdelta": 0.0001, "MMwindow": 10, "Lambda_mm": 0.2
                }
    
    for j in range(51, 52):
        random.seed(j)
        np.random.seed(j)
    
        start = time.time()
        
        h5_root = 'python_pyziabmc_tdelta_%d' % j
        h5dir = 'C:\\Users\\user\\Documents\\Agent-Based Models\\h5 files\\Trial 901\\'
        h5_file = '%s%s.h5' % (h5dir, h5_root)
    
        market1 = Runner(h5filename=h5_file, **settings)

        print('Run %d: %.1f seconds' % (j, time.time() - start))