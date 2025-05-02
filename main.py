import orderFlow
import json

if __name__ == "__main__":
    """
    Main function to execute the order flow analysis.
    """
    # Initialize the OrderFlow class with the CSV file
    orderFlow = orderFlow.OrderFlow('./first_25000_rows.csv')

    # print the order flow dataframe columns definition
    print(f"The definition of columns: \n{json.dumps(orderFlow.orderFlowDfColumns(), indent=4)}")

    # Generate best level OFI
    orderFlow.generate_OFI_0_h_i_t(i="AAPL")
    
    # Generate deeper level OFI
    orderFlow.generate_ofi_m_h_i_t(i="AAPL")
    
    # PCA of OFI
    orderFlow.generate_ofi_I_h_i_t(i="AAPL")

    