import asyncio
import aiohttp
import os
import time
import re
import json

class GithubUser:
	def __init__(self, username: str) -> None:
		self.username = username 
		self.repos = {}
		self.emails = []

		self.session = None

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
				
	async def get_commits(self, repo: dict) -> bool:
		async with self.session.get(f'https://api.github.com/repos/{self.username}/{repo}/commits') as response:
			if response.status != 200:
				print(f'[-] failed to get commits for: {repo}')
				return False

			data = await response.json()
			if not data:
				print(f'[-] no commits found for: {repo}')
				return False 

			for commit in data:
				self.repos[repo].append(f'{commit["html_url"]}.patch')

			return True 

	async def search_commit(self, commit_url: str) -> None:
		async with self.session.get(commit_url) as response:
			text = await response.text()
			emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)

			for email in emails:
				if email not in [entry['email'] for entry in self.emails] and 'users.noreply.github.com' not in email:
					self.emails.append({
						'email': email,
						'commit_url': commit_url
					})

async def main():
	username = str(input('[>] username: '))
	
	async with GithubUser(username) as user:
		start = time.time()

		if not await user.is_valid():
			return 

		if not await user.get_repos():
			return 

		await asyncio.gather(*[user.get_commits(repo) for repo in user.repos])

		commits = [commit_url for repo in user.repos for commit_url in user.repos[repo]]
		if not commits:
			return 

		await asyncio.gather(*[user.search_commit(commit_url) for repo in user.repos for commit_url in user.repos[repo]])

		end = time.time()
		print(f'[+] done, took: {end - start:.2f}s')

		if not user.emails:
			print('[-] did not find any exposed emails')
			return 
		
		print(f'[+] emails: {user.emails}')

if __name__ == "__main__":
	if os.name == 'nt':
		asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
		
	asyncio.run(main())