import requests
from datetime import datetime

class CryptoAPI:
    def __init__(self):
        self.coingecko_base = 'https://api.coingecko.com/api/v3'
    
    def get_crypto_price(self, coin_id='bitcoin', currency='usd'):
        try:
            url = f'{self.coingecko_base}/simple/price'
            params = {
                'ids': coin_id,
                'vs_currencies': currency,
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if coin_id in data:
                return {
                    'coin': coin_id,
                    'price': data[coin_id].get(currency, 0),
                    'change_24h': data[coin_id].get(f'{currency}_24h_change', 0),
                    'market_cap': data[coin_id].get(f'{currency}_market_cap', 0),
                    'currency': currency.upper(),
                    'timestamp': datetime.now().isoformat()
                }
            return None
        except Exception as e:
            print(f"Error fetching crypto price: {e}")
            return None
    
    def get_multiple_prices(self, coin_ids=['bitcoin', 'ethereum', 'binancecoin'], currency='usd'):
        try:
            url = f'{self.coingecko_base}/simple/price'
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': currency,
                'include_24hr_change': 'true'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for coin_id in coin_ids:
                if coin_id in data:
                    results.append({
                        'coin': coin_id,
                        'price': data[coin_id].get(currency, 0),
                        'change_24h': data[coin_id].get(f'{currency}_24h_change', 0),
                        'currency': currency.upper()
                    })
            return results
        except Exception as e:
            print(f"Error fetching multiple prices: {e}")
            return []
    
    def get_trending_coins(self):
        try:
            url = f'{self.coingecko_base}/search/trending'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            trending = []
            for item in data.get('coins', [])[:5]:
                coin = item.get('item', {})
                trending.append({
                    'id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'market_cap_rank': coin.get('market_cap_rank')
                })
            return trending
        except Exception as e:
            print(f"Error fetching trending coins: {e}")
            return []
    
    def search_coin(self, query):
        try:
            url = f'{self.coingecko_base}/search'
            params = {'query': query}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            coins = []
            for coin in data.get('coins', [])[:10]:
                coins.append({
                    'id': coin.get('id'),
                    'name': coin.get('name'),
                    'symbol': coin.get('symbol'),
                    'market_cap_rank': coin.get('market_cap_rank')
                })
            return coins
        except Exception as e:
            print(f"Error searching coin: {e}")
            return []
    
    def get_global_stats(self):
        try:
            url = f'{self.coingecko_base}/global'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get('data', {})
            
            return {
                'active_cryptocurrencies': data.get('active_cryptocurrencies', 0),
                'total_market_cap_usd': data.get('total_market_cap', {}).get('usd', 0),
                'total_volume_usd': data.get('total_volume', {}).get('usd', 0),
                'market_cap_change_24h': data.get('market_cap_change_percentage_24h_usd', 0)
            }
        except Exception as e:
            print(f"Error fetching global stats: {e}")
            return None
