"""
Order of the Stone - LAN Multiplayer System
Simple, easy-to-use multiplayer for local network gaming
"""

from .lan_server import LANServer
from .lan_client import LANClient

__all__ = ['LANServer', 'LANClient']

