import asyncio
import aiohttp
import os
import time
import re
import json

class GithubUser:
	def __init__(self, username: str) -> None:
		self.username = username 
		self.session = None

		self.repos = {}

	async def __aenter__(self) -> 'Searcher':
		if not self.session:
			self.session = aiohttp.ClientSession()
		return self

	async def __aexit__(self, *exception: object) -> None:
		if self.session:
			await self.session.close()

	async def is_valid(self) -> bool:
		async with self.session.get(f'https://github.com/{self.username}') as response:
			if response.status == 404:
				print('[-] invalid username')
				return False
			return True

	async def get_repos(self) -> bool:
		async with self.session.get(f'https://api.github.com/users/{self.username}/repos') as response:
			if response.status != 200:
				print('[-] failed to get repos data')
				return False

			data = await response.json()
			if not data:
				print('[-] user doesnt have any public repositories')
				return False 
			
			for repo in data:
				if repo['fork']:
					continue
				self.repos[repo['name']] = []
			return True
				
async def main():
	username = str(input('[>] username: '))
	
	async with GithubUser(username) as user:
		start = time.time()

		if not await user.is_valid():
			return 

		if not await user.get_repos():
			return 

if __name__ == "__main__":
	if os.name == 'nt':
		asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
		
	asyncio.run(main())