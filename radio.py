from discord import FFmpegPCMAudio, utils, Status
from discord.ext import commands
from discord.ext.tasks import loop

import os, random


class Radio(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

		self.template = {"choice_musique": 0, "joined": False, "paused": False, "resume": True, "stopped": False, "random": False}
		self.all_voices = {}
		self.all_musics = os.listdir(f'{os.getcwd()}/Music')

	def change_music(self, op: str):
		self.all_voices[self.vocalChannel.id]["choice_musique"] += 1 if op == '+' else -1
		if (self.all_voices[self.vocalChannel.id]["choice_musique"] >= len(self.all_musics)-1) if op == '+' else (self.all_voices[self.vocalChannel.id]["choice_musique"] <= -1):
			self.all_voices[self.vocalChannel.id]["choice_musique"] = 0 if op == '+' else len(self.all_musics)-1

	@staticmethod
	def play_music(music, voice):
		if voice.is_playing():
			voice.stop()
		sources = FFmpegPCMAudio(f'{os.getcwd()}/Music/{music}')
		return voice.play(sources)

	@commands.Cog.listener()
	async def on_raw_reaction_add(self, event):
		if event.message_id == self.bot.data[str(event.guild_id)]['message_radio_id']:
			guild = utils.get(self.bot.guilds, id= event.guild_id)
			textChannel = utils.get(guild.channels, id= event.channel_id)
			self.vocalChannel = utils.get(guild.voice_channels, id= event.member.voice.channel.id)
			message = textChannel.get_partial_message(event.message_id)
			self.all_voices[self.vocalChannel.id] = self.template

			# The bot join the vocal channel where is the user
			if str(event.emoji) == self.bot.emoji_add_bot:
				for member in self.vocalChannel.members:
					if self.bot.bot_id == member.id:
						await message.remove_reaction(event.emoji, event.member); return
				# join vocal
				self.voice = await self.vocalChannel.connect()
				self.all_voices[self.vocalChannel.id]["joined"] = True
				# set random value for first start of musique
				random_choice = random.randint(0, len(self.all_musics)-1)
				self.all_voices[self.vocalChannel.id]["choice_musique"] = random_choice

				self.play_music(self.all_musics[random_choice], self.voice)
				# Display "is used"
				await self.bot.change_activity(f"Musics 𝘊𝘩𝘪𝘭𝘭 & 𝘓𝘰-𝘍𝘪 | {self.bot.version}", Status.online)
				# Start loop for changing automatically the musique
				if not self.change_musique_loop.is_running():
					self.change_musique_loop.start()

			# If joined a vocal channel
			if self.all_voices[self.vocalChannel.id]["joined"]:
				# The bot leave the vocal channel
				if str(event.emoji) == self.bot.emoji_remove_bot:
					# leave vocal
					await guild.voice_client.disconnect()
					self.all_voices[self.vocalChannel.id]["joined"] = False
					# Display "is not used"
					await self.bot.change_activity(f"Musics 𝘊𝘩𝘪𝘭𝘭 & 𝘓𝘰-𝘍𝘪 | {self.bot.version}", Status.do_not_disturb)
					# Stop loop for changing automatically the musique
					if not self.change_musique_loop.is_being_cancelled():
						self.change_musique_loop.stop()

				# Change the music
				if str(event.emoji) == self.bot.emoji_next_music and (self.voice.is_playing()):
					if self.all_voices[self.vocalChannel.id]["random"] is False:
						self.change_music('+')
					else:
						self.all_voices[self.vocalChannel.id]["choice_musique"] = random.randint(0, len(self.all_musics)-1)
					self.play_music(self.all_musics[self.all_voices[self.vocalChannel.id]["choice_musique"]], self.voice)

				# Redu the music
				if str(event.emoji) == self.bot.emoji_previous_music and (self.voice.is_playing()):
					self.change_music('-')
					self.play_music(self.all_musics[self.all_voices[self.vocalChannel.id]["choice_musique"]], self.voice)

				# Stop the music
				if (str(event.emoji) == self.bot.emoji_stop_music) and (self.voice.is_playing()):
					self.all_voices[self.vocalChannel.id]["stopped"] = True
					self.all_voices[self.vocalChannel.id]["resume"] = False
					if not self.change_musique_loop.is_being_cancelled():
						self.change_musique_loop.stop()

				# Restart the music where is been stopped
				if (str(event.emoji) == self.bot.emoji_resume_music) and (not self.voice.is_playing()):
					self.play_music(self.all_musics[self.all_voices[self.vocalChannel.id]["choice_musique"]], self.voice)
					self.all_voices[self.vocalChannel.id]["stopped"] = False
					self.all_voices[self.vocalChannel.id]["resume"] = True
					if not self.change_musique_loop.is_running():
						self.change_musique_loop.start()

				# Set random selection of music
				if str(event.emoji) == self.bot.emoji_random_music:
					self.all_voices[self.vocalChannel.id]["random"] = True

			# Remove after an action on reaction below of radio message
			if str(event.emoji) not in [self.bot.emoji_random_music]:
				await message.remove_reaction(event.emoji, event.member)

	@commands.Cog.listener()
	async def on_raw_reaction_remove(self, event):
		# Radio message
		if event.message_id == self.bot.data[str(event.guild_id)]['message_radio_id']:
			# Random selection of music
			if (str(event.emoji) == self.bot.emoji_random_music) and (event.member is not None):
				self.all_voices[self.vocalChannel.id]["random"] = False

	@commands.Cog.listener()
	async def on_ready(self):
		await self.check_inactive.start()

	@loop(seconds= 2)
	async def change_musique_loop(self):
		await self.bot.wait_until_ready()

		# Changing automatically the music if the previous music is finished
		if self.all_voices[self.vocalChannel.id]["resume"] is True:
			if self.voice.is_playing() is False:
				if self.all_voices[self.vocalChannel.id]["random"] is False:
					self.change_music('+')
				else:
					self.all_voices[self.vocalChannel.id]["choice_musique"] = random.randint(0, len(self.all_musics) - 1)
				self.sources = FFmpegPCMAudio(f'./Music/{self.all_musics[self.all_voices[self.vocalChannel.id]["choice_musique"]]}')
				self.voice.play(self.sources)

	@loop(minutes= 2)
	async def check_inactive(self):
		await self.bot.wait_until_ready()

		for guild_id in self.bot.data:
			guild = utils.get(self.bot.guilds, id=int(guild_id))
			if guild is not None:
				textChannel = utils.get(guild.channels, id=self.bot.data[guild_id]["channel_radio"])
				member = utils.get(guild.members, id=self.bot.bot_id)
				message = textChannel.get_partial_message(self.bot.data[guild_id]["message_radio_id"])
				full_message = await message.fetch()
				list_reaction: list = full_message.reactions

				if member.voice is not None:
					if (self.count >= 3) or (self.voice.is_playing() is False):
						self.count = 0
					if self.count == 0:
						for react in list_reaction:
							if (str(react.emoji) == self.bot.emoji_random_music) and (react.count >= 2):
								async for user in react.users():
									if user.bot is False:
										await message.remove_reaction(self.bot.emoji_random_music, user) if (self.voice.is_playing()) is False else None
					await guild.voice_client.disconnect() if (len(member.voice.channel.members) == 1) and (self.count == 2) else None
					self.count += 1
				else:
					# Delete random function after logout of bot
					for react in list_reaction:
						if (str(react.emoji) == self.bot.emoji_random_music) and (react.count >= 2):
							async for user in react.users():
								if user.bot is False:
									await message.remove_reaction(react.emoji, user)