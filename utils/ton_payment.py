
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
class TONPayment:
    """Utility class for generating TON payment links"""
    
    def __init__(self):
        pass
    
    def create_payment_link(self, recipient_address, amount, comment=""):
        """
        Create a TON payment link
        
        Args:
            recipient_address: TON wallet address (EQ... or UQ...)
            amount: Amount in TON
            comment: Optional payment comment
            
        Returns:
            Payment link string or None if invalid
        """
        if not recipient_address or not isinstance(amount, (int, float)):
            return None
        
        # Validate TON address format
        if not ((recipient_address.startswith('EQ') or recipient_address.startswith('UQ')) 
                and len(recipient_address) == 48):
            return None
        
        # Generate TON payment link
        # Format: ton://transfer/<address>?amount=<amount>&text=<comment>
        base_url = f"ton://transfer/{recipient_address}"
        
        # Convert amount to nanotons (1 TON = 1,000,000,000 nanotons)
        nanotons = int(amount * 1_000_000_000)
        
        params = [f"amount={nanotons}"]
        
        if comment:
            # URL encode the comment
            import urllib.parse
            encoded_comment = urllib.parse.quote(comment)
            params.append(f"text={encoded_comment}")
        
        payment_link = f"{base_url}?{'&'.join(params)}"
        
        return payment_link
    
    def validate_ton_address(self, address):
        """
        Validate TON wallet address format
        
        Args:
            address: TON wallet address to validate
            
        Returns:
            Boolean indicating if address is valid
        """
        if not address or not isinstance(address, str):
            return False
        
        return ((address.startswith('EQ') or address.startswith('UQ')) 
                and len(address) == 48)
