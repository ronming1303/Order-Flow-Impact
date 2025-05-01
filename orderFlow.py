import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings("ignore")

class OrderFlow(object):
    def __init__(self, orderFlowFilePath: str, maximumDepth=10, h="1min"):
        self.orderFlowDf = pd.read_csv(orderFlowFilePath)
        self.stockSymbols = list(self.orderFlowDf['symbol'].unique())
        self.M = maximumDepth
        self.h = h
        
    def orderFlowDfColumns(self):
        self.columnsDict = {
            "ts_recv": "timestamp received",
            "ts_event": "timestamp sent from exchange",
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

    def generate_OFI_m_h_i_t(self, depth=0, i="AAPL"):
        assert i in self.stockSymbols, f"Symbol '{i}' not found"

        print(f"Generating OFI for stock {i} at depth {depth}")
        # copy the order flows of stock i
        orderFlowDf_i = self.orderFlowDf[self.orderFlowDf['symbol'] == i].copy()
        # sort the order flow by "sequence"
        orderFlowDf_i.sort_values(by=["sequence"], inplace=True)
        # if there are multiple lines at the same time, we only keep the last line which is fully updated
        orderFlowDf_i.drop_duplicates(subset=['ts_event'], keep='last', inplace=True)
        # add minute column
        if self.h == "1min":
            orderFlowDf_i['minute'] = pd.to_datetime(orderFlowDf_i['ts_event'], utc=True).dt.strftime('%Y-%m-%d %H:%M')
        else:
            KeyError(f"Unsupported time interval {self.h}. Only 1min is supported.")
        
        df_ofi_m_h_i_t = pd.DataFrame()
        # generate ofi_1_h_i for each minute
        for t, groupedDf in orderFlowDf_i.groupby('minute'):
            ofi_m_h_i_t = 0
            for n in range(1, len(groupedDf)):
                # get the current row
                currentRow = groupedDf.iloc[n]
                # get the previous row
                previousRow = groupedDf.iloc[n-1]
                p_m_b_i_n = currentRow[f'bid_px_0{depth}']
                p_m_a_i_n = currentRow[f'ask_px_0{depth}']
                q_m_b_i_n = currentRow[f'bid_sz_0{depth}']
                q_m_a_i_n = currentRow[f'ask_sz_0{depth}']
                p_m_b_i_n_1 = previousRow[f'bid_px_0{depth}']
                p_m_a_i_n_1 = previousRow[f'ask_px_0{depth}']
                q_m_b_i_n_1 = previousRow[f'bid_sz_0{depth}']
                q_m_a_i_n_1 = previousRow[f'ask_sz_0{depth}']
                # calculate the OF_m_b_i_n
                if p_m_b_i_n > p_m_b_i_n_1:
                    of_m_b_i_n = q_m_b_i_n
                elif p_m_b_i_n == p_m_b_i_n_1:
                    of_m_b_i_n = q_m_b_i_n - q_m_b_i_n_1
                else:
                    of_m_b_i_n = -1 * q_m_b_i_n
                # calculate the OF_m_a_i_n
                if p_m_a_i_n > p_m_a_i_n_1:
                    of_m_a_i_n = -1 * q_m_a_i_n
                elif p_m_a_i_n == p_m_a_i_n_1:
                    of_m_a_i_n = q_m_a_i_n - q_m_a_i_n_1
                else:
                    of_m_a_i_n = q_m_a_i_n
                # update the OFI
                ofi_m_h_i_t += of_m_b_i_n
                ofi_m_h_i_t -= of_m_a_i_n
                # update the Q^m in equation (3)
                q_m = q_m_b_i_n + q_m_a_i_n
            q_m = q_m / len(groupedDf)
                
            # add the OFI to the dataframe
            df_ofi_m_h_i_t = df_ofi_m_h_i_t.append({
                'minute': t,
                f'OFI_{depth}_h_i_t': ofi_m_h_i_t,
                f'q_{depth}': q_m,
                'symbol': i
            }, ignore_index=True)
            
        return df_ofi_m_h_i_t
    
    def generate_OFI_0_h_i_t(self, i="AAPL"):
        filename = f'processd_data/OFI_0_h_i_t/best_level_OFI_{i}.csv'
        if os.path.exists(filename):
            print(f"Already found: {filename}")
        else:
            df = self.generate_OFI_m_h_i_t(depth=0, i=i)[["minute", "symbol", "OFI_0_h_i_t"]]
            df.to_csv(filename)
            print(f"Saved: {filename}")
            
    def generate_ofi_m_h_i_t(self, i="AAPL"):
        # save the dataframe
        filename = f'processd_data/ofi_m_h_i_t/multi_level_ofi_{i}.csv'
        if os.path.exists(filename):
            print(f"Already found: {filename}")
        else:
            df = pd.DataFrame()
            for depth in range(self.M):
                df_m = self.generate_OFI_m_h_i_t(depth=depth, i=i)
                if len(df) == 0:
                    df = df_m
                else:
                    df = pd.merge(df, df_m, on=['minute', 'symbol'], how='outer')
            # weighted by Q_M
            df["Q_M"] = 0
            for depth in range(self.M):
                df["Q_M"] += df[f'q_{depth}']
                df.drop(columns=[f'q_{depth}'], inplace=True)
            df["Q_M"] = df["Q_M"] / self.M
            
            for depth in range(self.M):
                df[f'ofi_{depth}_h_i_t'] = df[f'OFI_{depth}_h_i_t'] / df['Q_M']
                df.drop(columns=[f'OFI_{depth}_h_i_t'], inplace=True)
            df.drop(columns=['Q_M'], inplace=True)
            
            df.to_csv(filename)
            print(f"Saved: {filename}")
        
        
orderFlow = OrderFlow('./first_25000_rows.csv')

# generate best level OFI
orderFlow.generate_OFI_0_h_i_t(i="AAPL")
# generate deeper level ofi
orderFlow.generate_ofi_m_h_i_t(i="AAPL")
# print(f"The definition of columns: \n{json.dumps(orderFlow.orderFlowDfColumns(), indent=4)}")
