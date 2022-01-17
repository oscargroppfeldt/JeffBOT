import discord
from discord.ext import commands
import os
import youtube_dl
import time
                       

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.voice_states = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.environ['TOKEN']

SFXlst = {"milk" : "https://youtu.be/xfl31la4f2E?t=1", 
		"bonk" :"https://www.youtube.com/watchv=gwxTZaa3NgIab_channel=YerBoiLloris",
		"what" : "https://www.youtube.com/watch?v=pYaX22MTp8gab_channel=MemeSounds"}

bonk_lst = []
knownUserAlias = {}
user_stats = {}

class MemberStat:
	def __init__(self, member):
		self.member = member
		self.times_joined = 0
		self.time_spent_in_discord_seconds = 0
		self.avg_time_per_session_seconds = 0
		self.num_of_afk = 0
		self.last_join_time = 0
		self.messages_sent = 0
		if(not isinstance(member, str)):
			self.user_str = self.member.name.split('#')[0]
		else:
			self.user_str = "Dummy"
	
	def on_join(self):
		self.times_joined += 1

	def update_user_time(self):
		current_time = time.time()
		time_delta = current_time - self.last_join_time
		self.last_join_time = current_time
		self.time_spent_in_discord_seconds += time_delta


	def __str__(self):
		time_lst = seconds_converter(self.time_spent_in_discord_seconds)
		time_str = f"{time_lst[2]} timmar, {time_lst[1]} minuter, {int(time_lst[0])} sekunder"
		
		self.avg_time_per_session_seconds =  self.time_spent_in_discord_seconds / self.times_joined 
		
		time_lst_avg = seconds_converter(self.avg_time_per_session_seconds)
		time_avg_str = f"{time_lst_avg[2]} timmar, {time_lst_avg[1]} minuter, {int(time_lst_avg[0])} sekunder"


		return f"____Statistik för {self.user_str}____:\n\tTotal tid i voice:\n\t\t{time_str}\n\tEtt snitt på:\n\t\t{time_avg_str} per session\n\tGått afk:\n\t\t{self.num_of_afk} gång(er)\n\tSkickat {self.messages_sent} meddelanden"

def seconds_converter(seconds):
	hours = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return[seconds, minutes, hours]

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	user_stats[1234567890] = MemberStat("Dummy Jonson")
	user_stats[1234567891] = MemberStat("Dummy Berenstein")
	user_stats[1234567892] = MemberStat("Dummy Smith")
	user_stats[1234567890].avg_time_per_session_seconds = 666
	user_stats[1234567891].avg_time_per_session_seconds = 1337
	user_stats[1234567892].avg_time_per_session_seconds = 420
	user_stats[1234567890].time_spent_in_discord_seconds = 420
	user_stats[1234567891].time_spent_in_discord_seconds = 666
	user_stats[1234567892].time_spent_in_discord_seconds = 1337
	user_stats[1234567890].user_str = "Dummy Smith"
	user_stats[1234567891].user_str = "Dummy Berenstein"
	user_stats[1234567892].user_str = "Dummy Jonson"


# Check if joining user has been bonked since their last connection
# and logs their stats
@bot.event
async def on_voice_state_update(user: discord.Member, before, after):
	# if the coroutine is activated for other reasons than a user moving voice-channel, ignore
	if before.channel == after.channel:
		return

	if before.channel is None:
		if user in bonk_lst:
			bonk(user.Guild.system_channel, user)

	if before.channel is None and not after.afk:

		if not user.id in user_stats:
			new_user = MemberStat(user)
			user_stats[user.id] = new_user
			stats = new_user
		else:
			stats = user_stats[user.id]

		stats.times_joined += 1
		join_time = time.time()
		stats.last_join_time = join_time
	
	elif before.channel is not None and after.afk:
		stats = user_stats[user.id]
		stats.num_of_afk += 1
		afk_time = time.time()
		time_delta = afk_time - stats.last_join_time
		stats.time_spent_in_discord_seconds += time_delta

	elif before.afk and after.channel is not None:
		stats = user_stats[user.id]
		stats.times_joined += 1
		join_time = time.time()
		stats.last_join_time = join_time

@bot.event
async def on_message(msg):
	user = msg.author
	if not msg.is_system() and user.id is not bot.user.id:
		stats = user_stats[user.id]
		stats.messages_sent += 1
	await bot.process_commands(msg)

def play_audio(ctx, song):
	ydl_opts = {
			'format': 'bestaudio/best',
			'postprocessors': [{
				'key': 'FFmpegExtractAudio',
				'preferredcodec': 'mp3',
				'preferredquality': '192',
			}],
		}
	

	if not os.ospath.isfile(f"{song}.mp3"):
		url = SFXlst[song]
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download([url])
			for file in os.listdir("./"):
				if file.endswith(".mp3"):
					os.rename(file, f"{song}.mp3")

	ctx.voice_client.play(discord.FFmpegPCMAudio(f"{song}.mp3"))


# Moves the given user to the afk-channel
# And plays a sound
@bot.command()
async def bonk(ctx, user_str):

	if user_str in knownUserAlias:
		user = knownUserAlias[user_str]
	else:
		try:
			user = ctx.guild.get_member_named(user_str)
		except TypeError:
			user = user_str

	if user.id == 138687184302637058 and ctx.message.author.id != 138687184302637058:
		await ctx.send("Mmm jo tjena va.")
		new_bonk = ctx.message.author
		await bonk(ctx, new_bonk)
		return
	
	if user.id == 189070175448858625 and ctx.message.author.id != 189070175448858625:
		await ctx.send(f"Du bör passa dig jävligt noga nu {ctx.message.author.name.split('#')[0]}.")
		return
	
	await ctx.author.voice.channel.connect()

	play_audio(ctx, "bonk")
	
	voice_state = user.voice
	try:
		if voice_state is None:
			await ctx.send(str(user).split('#')[0] + " är ju inte här, bonkar honom när han kommer tillbaka.\n ;)")
			if user not in bonk_lst:
				bonk_lst.append(user)

		elif user.voice.channel:
			if user_str in knownUserAlias:
				await ctx.send(f"Nu jävlar ska {user_str} få mysa lite med mig.")
				await user.move_to(ctx.guild.afk_channel)
			else:
				await ctx.send(f"Nu jävlar ska {str(user).split('#')[0]} få lär kännna mig lite bättre.")
				await user.move_to(ctx.guild.afk_channel)
	except discord.ext.commands.errors.MemberNotFound:
		await ctx.send("Vem fan är det?")
	
	await ctx.voice_client.disconnect()


# Adds an alias for user
@bot.command()
async def addAlias(ctx, user: discord.Member, arg: str):
	knownUserAlias[arg] = user
	await ctx.send(f"HAHAHA kallar ni {str(user).split('#')[0]} för {arg}?\nAja okej då...")



# TODO: Uppdatera tidsstattistik för user
@bot.command()
async def stats(ctx, user: discord.Member):
	stats = user_stats[user.id]
	stats.update_user_time()
	await ctx.send(stats.__str__())


@bot.command()
async def leaderboard(ctx):
	members_sorted_tot_time = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].time_spent_in_discord_seconds)}
	members_sorted_avg_time = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].avg_time_per_session_seconds)}
	members_sorted_afk_num = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].num_of_afk)}
	
	message_tot_time = "____ Trogna nördar ____\n \
		1. {user_1}, {time_1}\n\
		2. {user_2}, {time_2}\n\
		3. {user_3}, {time_3}\n".format(\
			user_1 = list(members_sorted_tot_time.values())[2].user_str, time_1 = list(members_sorted_tot_time.values())[2].time_spent_in_discord_seconds,\
			user_2 = list(members_sorted_tot_time.values())[1].user_str, time_2 = list(members_sorted_tot_time.values())[1].time_spent_in_discord_seconds,\
			user_3 = list(members_sorted_tot_time.values())[0].user_str, time_3 = list(members_sorted_tot_time.values())[0].time_spent_in_discord_seconds)

	message_avg_time = "____ Fyrkantiga ögon ____\n \
		1. {user_1}, {time_1}\n\
		2. {user_2}, {time_2}\n\
		3. {user_3}, {time_3}\n".format(\
			user_1 = list(members_sorted_avg_time.values())[2].user_str, time_1 = list(members_sorted_avg_time.values())[2].avg_time_per_session_seconds,\
			user_2 = list(members_sorted_avg_time.values())[1].user_str, time_2 = list(members_sorted_avg_time.values())[1].avg_time_per_session_seconds,\
			user_3 = list(members_sorted_avg_time.values())[0].user_str, time_3 = list(members_sorted_avg_time.values())[0].avg_time_per_session_seconds)

	message_afk_num = "____ \"BRB runka\" ____\n \
		1. {user_1}, {time_1}\n\
		2. {user_2}, {time_2}\n\
		3. {user_3}, {time_3}\n".format(\
			user_1 = list(members_sorted_afk_num.values())[2].user_str, time_1 = list(members_sorted_afk_num.values())[2].num_of_afk,\
			user_2 = list(members_sorted_afk_num.values())[1].user_str, time_2 = list(members_sorted_afk_num.values())[1].num_of_afk,\
			user_3 = list(members_sorted_afk_num.values())[0].user_str, time_3 = list(members_sorted_afk_num.values())[0].num_of_afk)
			
	message_to_send = message_tot_time + "\n" + message_avg_time + "\n" + message_afk_num
	await ctx.send(message_to_send)
	



bot.run(TOKEN)