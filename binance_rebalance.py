from binance.client import Client


class BinanceRebalance:

    __set_weights:dict
    __base_asset = 'USDT'

    def __init__(self):
        api_key = '<XXXXXXXXXXXXXXX>'
        api_secret = '<XXXXXXXXXXXXXXX>'
        client = Client(api_key, api_secret)
        api_key = '<XXXXXXXXXXXXXXX>'
        api_secret = '<XXXXXXXXXXXXXXX>'
        trade_client = Client(api_key, api_secret)

    def rebalance_portfolio(self):
        curr_port = self.get_current_port()
        self.rebalance_sell_action(curr_port, self.get_set_weights())
        self.rebalance_buy_action(curr_port, self.get_set_weights())
    
    def get_set_weights(self):
        return self.__set_weights
    
    def get_base_asset(self) -> str:
        return self.__base_asset

    def rebalance_sell_action(self, curr_port, set_weights):
        for asset in curr_port:
            if asset['symbol'] == self.get_base_asset():
                continue

            set_weight=0.0
            if asset['symbol'] in set_weights.keys():
                set_weight = set_weights[asset['symbol']]

            adj_size = calc_adj_size(
                current_amt=asset['amount'],
                total_balance=get_total_balance(curr_port),
                set_weight=set_weight,
                asset_price=curr_price[asset['symbol']+'USDT'],
            )

            if adj_size < 0.0:
                amt_to_sell=abs(adj_size)
                market_sell_order(pair=asset['symbol']+'USDT', quantity=amt_to_sell)
        
    def rebalance_buy_action(curr_port, set_weights):
        for symbol, weight in set_weights.items():
            if symbol == 'USDT':
                print('skip USDT')
                continue
            curr_asset_info = [x for x in curr_port if x['symbol'] == symbol]
            current_amt = 0.0
            if curr_asset_info:
                current_amt=curr_asset_info[0]['amount']
            adj_size = calc_adj_size(
                current_amt=current_amt,
                total_balance=get_total_balance(curr_port),
                set_weight=set_weights[symbol],
                asset_price=curr_price[symbol+'USDT'],
            )
            if adj_size > 0.0:
                market_buy_order(pair=symbol+'USDT', quantity=adj_size)

    def get_curr_price():
        return {x['symbol']:x['price'] for x in client.get_all_tickers() if x['symbol'].endswith('USDT')}
    
    def get_total_balance(curr_port):
        total_port_balance = sum([float(x['usd_amount']) for x in curr_port])
        return total_port_balance
    
    def get_current_port():
        info = client.get_account()
        curr_price = get_curr_price()
        curr_port=[]
        for asset in info['balances']:
            if float(asset['free']) and asset['asset'] in coin_list:
                asset_info={}
                asset_info['symbol']=asset['asset']
                asset_info['amount']=asset['free']
                asset_info['usd_amount']=float(asset['free'])
                if not asset['asset'] == 'USDT':
                    asset_info['usd_amount']=float(asset['free'])*float(curr_price[asset['asset']+'USDT'])
                if float(asset_info['usd_amount']) > 10.0:
                    curr_port.append(asset_info)
        # return curr_port 
        for i in range(len(curr_port)):
            curr_port[i]['weight'] = curr_port[i]['usd_amount'] / get_total_balance(curr_port)
        return curr_port

    def calc_adj_size(current_amt, total_balance, set_weight, asset_price):
        set_amt = (float(total_balance)*0.996 * float(set_weight)) / float(asset_price)
        return  set_amt - float(current_amt)

    def get_trade_size_info():
        return [{
            'symbol':x['symbol'][:-len('USDT')],
            'tickSize':x['filters'][0]['tickSize'],
            'stepSize':x['filters'][2]['stepSize'],
        } for x in exchange_info['symbols'] if x['symbol'].endswith('USDT')]
    
    def market_buy_order(pair, quantity):
        trade_size_info = get_trade_size_info()
        min_param_step = [x['stepSize'] for x in  trade_size_info if x['symbol'] == pair[:-4]][0]
        round_qty = round_param(param_size=quantity, min_param_step=min_param_step)
        print(f'buy {pair}: {round_qty}')
        if float(round_qty):
            trade_client.order_market_buy(symbol=pair, quantity=float(round_qty))

    def market_sell_order(pair, quantity):
        trade_size_info = get_trade_size_info()
        min_param_step = [x['stepSize'] for x in  trade_size_info if x['symbol'] == pair[:-4]][0]
        round_qty = round_param(param_size=quantity, min_param_step=min_param_step)
        print(f'sell {pair}: {float(round_qty)}')
        if float(round_qty):
            trade_client.order_market_sell(symbol=pair, quantity=round_qty)


    # from decimal import Decimal as d
    def round_param(param_size, min_param_step):
            param_size_str = str(param_size)
            min_param_step_str = str(min_param_step)
            round_qty = d(param_size_str) - (d(param_size_str)%d(min_param_step_str))
            if round_qty < d(min_param_step_str):
                    round_qty = 0.0
            return float(round_qty)

