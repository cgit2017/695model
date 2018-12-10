from enum import Enum


class Side(Enum):
    BID = 1
    ASK = 2
    
    
class OType(Enum):
    ADD = 1
    CANCEL = 2
    MODIFY = 3
    
    
class TType(Enum):
    NoiseTrader = 0
    FundamentalTrader = 1
    MomentumTrader = 2
    MarketMaker = 3
    