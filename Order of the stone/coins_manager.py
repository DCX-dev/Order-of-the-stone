import json
import os
from typing import Optional

class CoinsManager:
    def __init__(self, coins_file="coins.json"):
        self.coins_file = coins_file
        self.coins = 0
        self.username = ""
        self.load_coins()
    
    def load_coins(self):
        """Load coins from the JSON file"""
        try:
            if os.path.exists(self.coins_file):
                with open(self.coins_file, 'r') as f:
                    data = json.load(f)
                    self.coins = data.get('coins', 0)
                    self.username = data.get('username', '')
                    print(f"💰 Loaded {self.coins} coins for user: {self.username}")
            else:
                print("💰 No coins file found, starting with 0 coins")
        except Exception as e:
            print(f"⚠️ Error loading coins: {e}")
            self.coins = 0
            self.username = ""
    
    def save_coins(self):
        """Save coins to the JSON file"""
        try:
            data = {
                'coins': self.coins,
                'username': self.username
            }
            with open(self.coins_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"💰 Saved {self.coins} coins for user: {self.username}")
        except Exception as e:
            print(f"⚠️ Error saving coins: {e}")
    
    def get_coins(self) -> int:
        """Get current coin balance"""
        return self.coins
    
    def add_coins(self, amount: int):
        """Add coins to balance"""
        if amount > 0:
            self.coins += amount
            print(f"💰 Added {amount} coins! New balance: {self.coins}")
            self.save_coins()
        else:
            print(f"⚠️ Cannot add negative coins: {amount}")
    
    def spend_coins(self, amount: int) -> bool:
        """Spend coins if enough are available"""
        if amount <= 0:
            print(f"⚠️ Invalid amount to spend: {amount}")
            return False
        
        if self.coins >= amount:
            self.coins -= amount
            print(f"💰 Spent {amount} coins! New balance: {self.coins}")
            self.save_coins()
            return True
        else:
            print(f"❌ Not enough coins! Need {amount}, have {self.coins}")
            return False
    
    def set_username(self, username: str):
        """Set the username for this coin account"""
        self.username = username
        self.save_coins()
        print(f"👤 Username set to: {username}")
    
    def can_afford(self, amount: int) -> bool:
        """Check if player can afford an item"""
        return self.coins >= amount
    
    def get_formatted_balance(self) -> str:
        """Get formatted coin balance string"""
        if self.coins >= 1000000:
            return f"{self.coins/1000000:.1f}M"
        elif self.coins >= 1000:
            return f"{self.coins/1000:.1f}K"
        else:
            return str(self.coins)
