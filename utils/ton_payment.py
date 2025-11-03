
import requests
import time
from datetime import datetime

class TONPayment:
    def __init__(self):
        self.toncenter_api = 'https://toncenter.com/api/v2'
        
    def validate_address(self, address):
        """Validate TON wallet address format"""
        if not address:
            return False
        if not (address.startswith('EQ') or address.startswith('UQ')):
            return False
        if len(address) != 48:
            return False
        return True
    
    def get_transaction_info(self, address, limit=10):
        """Get recent transactions for a TON address"""
        try:
            url = f'{self.toncenter_api}/getTransactions'
            params = {
                'address': address,
                'limit': limit
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except Exception as e:
            print(f"Error fetching TON transactions: {e}")
            return []
    
    def verify_payment(self, sender_address, receiver_address, amount, transaction_hash=None):
        """Verify a TON payment transaction"""
        try:
            transactions = self.get_transaction_info(receiver_address, limit=20)
            
            for tx in transactions:
                # Check if transaction matches
                in_msg = tx.get('in_msg', {})
                source = in_msg.get('source', '')
                value = int(in_msg.get('value', 0)) / 1e9  # Convert from nanotons
                
                # Match sender and amount
                if source == sender_address and abs(value - amount) < 0.01:
                    return {
                        'verified': True,
                        'transaction_hash': tx.get('transaction_id', {}).get('hash'),
                        'amount': value,
                        'timestamp': tx.get('utime', 0)
                    }
            
            return {'verified': False, 'error': 'Transaction not found'}
        except Exception as e:
            print(f"Error verifying TON payment: {e}")
            return {'verified': False, 'error': str(e)}
    
    def get_balance(self, address):
        """Get TON balance for an address"""
        try:
            url = f'{self.toncenter_api}/getAddressBalance'
            params = {'address': address}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            balance = int(data.get('result', 0)) / 1e9
            return balance
        except Exception as e:
            print(f"Error fetching TON balance: {e}")
            return 0
    
    def create_payment_link(self, receiver_address, amount, comment=''):
        """Create a TON payment deep link"""
        if not self.validate_address(receiver_address):
            return None
        
        # Convert to nanotons
        nanotons = int(amount * 1e9)
        
        # Create ton:// link
        link = f"ton://transfer/{receiver_address}"
        params = []
        if nanotons > 0:
            params.append(f"amount={nanotons}")
        if comment:
            params.append(f"text={comment}")
        
        if params:
            link += "?" + "&".join(params)
        
        return link
