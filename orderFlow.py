import pandas as pd
import numpy as np
import json

class OrderFlow(object):
    def __init__(self, orderFlowFilePath: str):
        self.orderFlowDf = pd.read_csv(orderFlowFilePath)
        
    def orderFlowDfColumns(self):
        self.columnsDict = {
            "ts_recv": "timestamp received",
            "ts_send": "timestamp sent from exchange",
            "rtype": "Not clear, always equal to 10",
            "publisher_id": "ID of the publisher, always equal to 2",
            "instrument_id": "ID of the instrument, always equal to 38",
            "action": "C(ancel), A(dd), T(rade)",
            "side": "A(sk), B(id),or N(eutral): Neutral does not affect the order book snapshot",
            "depth": "depth position of the action",
            "price": "price of the action",
            "size": "size of the action",
            "flags": "130, 0, 128?",
            "ts_in_delta": "time delay of ts_recev to ts_send",
            "sequence": "sequence number of the action",
            "bid_px_00": "snapshot of the orderbook before this action. Note: if there are mutiple lines at the same time, the orderbook is not updated until the last line!!!",
            "symbol": "symbol of the instrument, always equal to AAPL",
        }
        return self.columnsDict


orderFlow = OrderFlow('./first_25000_rows.csv')
print(f"The definition of columns: \n{json.dumps(orderFlow.orderFlowDfColumns(), indent=4)}")