import asyncio
import random
import ssl
import json
import time
import uuid
import aiohttp
from dataclasses import dataclass
from typing import List, Optional
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from pathlib import Path
from datetime import datetime

@dataclass
class ProxyConfig:
    uri: str
    server_hostname: str
    version: str = "4.28.1"
    device_type: str = "desktop"

class ProxyBot:
    def __init__(self, config: ProxyConfig):
        self.config = config
        self.user_agent = UserAgent(os='windows', platforms='pc', browsers='chrome')
        self.session_start = datetime.now()
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with rotation and structured format"""
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True)
        logger.add(
            log_path / "proxy_bot_{time}.log",
            rotation="500 MB",
            retention="7 days",
            level="INFO"
        )

    @staticmethod
    def load_user_id() -> str:
        """Load user ID from file or prompt user to create one"""
        userid_file = Path('userid.txt')
        
        if not userid_file.exists():
            logger.warning("userid.txt not found")
            user_id = input('Please enter your user ID: ').strip()
            
            if not user_id:
                raise ValueError("User ID cannot be empty")
            
            # Save the user ID
            userid_file.write_text(user_id)
            logger.info("User ID saved to userid.txt")
            return user_id
        
        user_id = userid_file.read_text().strip()
        if not user_id:
            raise ValueError("Invalid user ID in userid.txt. User ID cannot be empty")
        
        # Hanya menampilkan 10 karakter pertama dan 5 karakter terakhir dari user ID
        id_length = len(user_id)
        if id_length > 15:  # Jika ID cukup panjang untuk dimasking
            logger.info(f"Login sebagai: {user_id[:10]}...{user_id[-5:]}")
        else:  # Jika ID terlalu pendek, tampilkan apa adanya
            logger.info(f"Login sebagai: {user_id}")
        return user_id

    async def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with proper settings"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    def get_headers(self) -> dict:
        """Generate headers with random user agent"""
        return {
            "User-Agent": self.user_agent.random,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

    async def send_ping(self, websocket):
        """Send periodic ping messages"""
        while True:
            try:
                message = {
                    "id": str(uuid.uuid4()),
                    "version": "1.0.0",
                    "action": "PING",
                    "data": {}
                }
                logger.debug(f"Sending ping: {message}")
                await websocket.send(json.dumps(message))
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in ping: {e}")
                break

    async def handle_message(self, message: dict, websocket, device_id: str, user_id: str, headers: dict):
        """Handle different types of websocket messages"""
        try:
            action = message.get("action")
            if action == "AUTH":
                auth_response = {
                    "id": message["id"],
                    "origin_action": "AUTH",
                    "result": {
                        "browser_id": device_id,
                        "user_id": user_id,
                        "user_agent": headers['User-Agent'],
                        "timestamp": int(time.time()),
                        "device_type": self.config.device_type,
                        "version": self.config.version,
                    }
                }
                await websocket.send(json.dumps(auth_response))
                logger.info(f"Authenticated device: {device_id}")
            
            elif action == "PONG":
                pong_response = {
                    "id": message["id"],
                    "origin_action": "PONG"
                }
                await websocket.send(json.dumps(pong_response))
                logger.debug("Pong sent")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise

    async def connect_to_wss(self, socks5_proxy: str, user_id: str):
        """Establish and maintain websocket connection"""
        device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
        retry_count = 0
        max_retries = 5
        
        while True:
            try:
                await asyncio.sleep(random.uniform(1, 3))
                headers = self.get_headers()
                ssl_context = await self.create_ssl_context()
                
                uri = random.choice([
                    f"wss://{self.config.server_hostname}:4444/",
                    f"wss://{self.config.server_hostname}:4650/"
                ])

                proxy = Proxy.from_url(socks5_proxy)
                
                async with proxy_connect(
                    uri,
                    proxy=proxy,
                    ssl=ssl_context,
                    server_hostname=self.config.server_hostname,
                    extra_headers=headers
                ) as websocket:
                    
                    logger.info(f"Connected to {uri} via {socks5_proxy}")
                    retry_count = 0  # Reset retry counter on successful connection
                    
                    ping_task = asyncio.create_task(self.send_ping(websocket))
                    
                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            await self.handle_message(message, websocket, device_id, user_id, headers)
                    
                    except Exception as e:
                        logger.error(f"Connection error: {e}")
                        ping_task.cancel()
                        raise
                        
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Max retries reached for proxy {socks5_proxy}. Stopping.")
                    break
                    
                wait_time = min(300, 2 ** retry_count)  # Exponential backoff
                logger.warning(f"Connection failed. Retrying in {wait_time}s... ({retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)

async def main():
    # Load configuration
    config = ProxyConfig(
        uri="wss://proxy.wynd.network",
        server_hostname="proxy.wynd.network"
    )
    
    bot = ProxyBot(config)
    
    try:
        # Load user ID from file
        user_id = bot.load_user_id()
        print(f"\n{'='*36}")
        
        # Menampilkan user ID dengan format yang sesuai panjangnya
        id_length = len(user_id)
        if id_length > 15:
            print(f"Login sebagai: {user_id[:10]}...{user_id[-5:]}")
        else:
            print(f"Login sebagai: {user_id}")
            
        print(f"{'='*36}\n")
            
        proxy_file = Path('local_proxies.txt')
        if not proxy_file.exists():
            raise FileNotFoundError("local_proxies.txt not found")
            
        local_proxies = proxy_file.read_text().splitlines()
        if not local_proxies:
            raise ValueError("No proxies found in local_proxies.txt")
            
        logger.info(f"Starting bot with {len(local_proxies)} proxies")
        
        tasks = [
            asyncio.ensure_future(bot.connect_to_wss(proxy, user_id))
            for proxy in local_proxies
        ]
        
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
