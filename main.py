import discord
from discord.ext import commands
import os
import asyncio
import youtube_dl
import time
import logger
                       

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.voice_states = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.environ['TOKEN']

SFXlst = {"milk" : "https://youtu.be/xfl31la4f2E?t=1", 
		"bonk" :"https://www.youtube.com/watch?v=gwxTZaa3NgI&ab_channel=YerBoiLloris",
		"what" : "https://www.youtube.com/watch?v=pYaX22MTp8gab_channel=MemeSounds"}

bonk_lst = []
knownUserAlias = {}
user_stats = {}


log = logger.Logger()
log.init()

"""
	TODO: 
	Build system for updating saved statistics
	Create system for updating bot from github during of-hours

"""

class MemberStat:
	def __init__(self, member):
		self.member = member
		self.times_joined = 0
		self.time_spent_in_discord_seconds = 0
		self.avg_time_per_session_seconds = 0
		self.num_of_afk = 0
		self.last_join_time = 0
		self.messages_sent = 0
		self.last_stream_time = 0
		self.time_spent_streaming = 0
		if(not isinstance(member, str)):
			self.user_str = self.member.name.split('#')[0]
		else:
			self.user_str = "Dummy"

	def get_user_stats_csv(self):
		res = f"{self.member.id},\n"
		res += f"{self.times_joined},\n"
		res += f"{self.time_spent_in_discord_seconds},\n"
		res += f"{self.avg_time_per_session_seconds},\n"
		res += f"{self.num_of_afk},\n"
		res += f"{self.last_join_time},\n"
		res += f"{self.messages_sent},\n"
		res += f"{self.last_stream_time},\n"
		res += f"{self.time_spent_streaming},\n"
		return res
	
	def update_user_time(self):
		current_time = time.time()
		time_delta = current_time - self.last_join_time
		self.last_join_time = current_time
		self.time_spent_in_discord_seconds += time_delta


	def __str__(self):
		time_lst = seconds_converter(self.time_spent_in_discord_seconds)
		time_str = f"{time_lst[2]} timmar, {time_lst[1]} minuter, {time_lst[0]} sekunder"
		
		self.avg_time_per_session_seconds = self.time_spent_in_discord_seconds / self.times_joined
		
		time_lst_avg = seconds_converter(self.avg_time_per_session_seconds)
		time_avg_str = f"{time_lst_avg[2]} timmar, {time_lst_avg[1]} minuter, {time_lst_avg[0]} sekunder"



		return f"Statistik f??r {self.user_str}:\nTotal tid i voice: {time_str}\nDet motsvarar ett snitt p?? {time_avg_str} per session \
				\nG??tt afk {self.num_of_afk} g??nger\nSkickat {self.messages_sent} meddelanden"

def seconds_converter(seconds):
	hours = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return[int(seconds), int(minutes), int(hours)]

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	await read_stats()
	await save_stats()


# Check if joining user has been bonked since their last connection
# and logs their stats
@bot.event
async def on_voice_state_update(user: discord.Member, before, after):

	if not before.self_stream and after.self_stream:
		time_stamp = time.time()
		user_stats[user.id].last_stream_time = time_stamp

	if not after.self_stream and before.self_stream:
		stats = user_stats[user.id]
		time_delta = time.time() - stats.last_stream_time
		stats.time_spent_streaming += time_delta

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

	elif before.channel is not None and after.channel is None:
		stats = user_stats[user.id]
		time_stamp = time.time()
		stats.time_spent_in_discord_seconds += time_stamp - stats.last_join_time
		stats.avg_time_per_session_seconds = stats.time_spent_in_discord_seconds / stats.times_joined
	
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


	elif not before.afk and after.channel is None:
		stats = user_stats[user.id]
		time_delta = time.time() - stats.last_join_time
		stats.time_spent_in_discord_seconds += time_delta
		if before.self_stream:
			stream_time_delta = time.time() - stats.last_stream_time
			stats.time_spent_streaming += stream_time_delta



@bot.event
async def on_message(msg):
	user = msg.author
	if not user.bot and not msg.is_system():
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
	

	if not os.path.isfile(f"{song}.mp3"):
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
		await ctx.send(f"Du b??r passa dig j??vligt noga nu {ctx.message.author.name.split('#')[0]}.")
		return
	
	voice_state = user.voice
	try:
		if voice_state is None:
			await ctx.send(str(user).split('#')[0] + " ??r ju inte h??r, bonkar honom n??r han kommer tillbaka.\n ;)")
			if user not in bonk_lst:
				bonk_lst.append(user)

		elif user.voice.channel:
			if user_str in knownUserAlias:
				await ctx.send(f"Nu j??vlar ska {user_str} f?? mysa lite med mig.")
				await user.move_to(ctx.guild.afk_channel)
			else:
				await ctx.send(f"Nu j??vlar ska {str(user).split('#')[0]} f?? l??r k??nnna mig lite b??ttre.")
				await user.move_to(ctx.guild.afk_channel)
				
		await ctx.author.voice.channel.connect()

		play_audio(ctx, "bonk")
		
		await ctx.voice_client.disconnect()

	except discord.ext.commands.errors.MemberNotFound:
		await ctx.send("Vem fan ??r det?")
	

# Adds an alias for user
@bot.command()
async def addAlias(ctx, user: discord.Member, arg: str):
	knownUserAlias[arg] = user
	await ctx.send(f"HAHAHA kallar ni {str(user).split('#')[0]} f??r {arg}?\nAja okej d??...")



@bot.command()
async def stats(ctx, *args : discord.Member):

	log.log(f"{ctx.author} called !stats on {args}")

	if not args:
		user = ctx.author
		stats = user_stats[user.id]
		if user.voice is not None and not user.voice.afk:
			stats.update_user_time()
		await ctx.send(stats.__str__())
	else:
		for user in args:
			stats = user_stats[user.id]
			if user.voice is not None and not user.voice.afk:
				stats.update_user_time()
			await ctx.send(stats.__str__())


@bot.command()
async def stat(ctx, stat, *args : discord.Member):

	log.log(f"{ctx.author} called !stat with stat {stat} on {args}")

	for user in args:
		if not isinstance(user, discord.Member):
			await ctx.send(f"{user} ??r inte en medlem i den h??r discorden\n(St??mmer inte detta? Skriv till Ogge att han ??r dum isf")
			log.log(f"Error in !stat: {user} is not discord.Member")
			continue
		
		usr_name = user.name.split('#')[0]
		match stat:
			case "stream":
				stat = user_stats[user.id].time_spent_streaming
				time = seconds_converter(stat)
				await ctx.send(f"{usr_name} har str??mmat:\n{time[2]} timmar, {time[1]} minuter och {time[0]} sekunder")
			case "msg":
				stat = user_stats[user.id].messages_sent
				await ctx.send(f"{usr_name} har skickat {stat} meddelanden")
			case "time":
				stats = user_stats[user.id]
				if user.voice is not None and not user.voice.afk:
					stats.update_user_time()
				stat = stats.time_spent_in_discord_seconds
				time = seconds_converter(stat)
				await ctx.send(f"{usr_name} har h??ngt i discord i {time[2]} timmar, {time[1]} minuter och {time[0]} sekunder")
			case _:
				await ctx.send("Anv??nd !stat stream/msg/time [anv??ndare]\nf??r tid streamad/ antal meddelanden/ tid i discord (ej afk tid) hos anv??ndarna")
				return





@bot.command()
async def leaderboard(ctx):

	log.log(f"{ctx.author} called !leaderboard")

	members_sorted_tot_time = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].time_spent_in_discord_seconds)}
	members_sorted_avg_time = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].avg_time_per_session_seconds)}
	members_sorted_str_time = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].time_spent_streaming)}
	members_sorted_afk_num = {k: v for k, v in sorted(user_stats.items(), key = lambda item: item[1].num_of_afk)}
	
	users_tot = list(members_sorted_tot_time.values())[-3:]
	users_avg = list(members_sorted_avg_time.values())[-3:]
	users_str = list(members_sorted_str_time.values())[-3:]
	users_afk = list(members_sorted_afk_num.values())[-3:]

	# TOTAL TIME
	time1 = seconds_converter(users_tot[-1].time_spent_in_discord_seconds)
	time2 = seconds_converter(users_tot[-2].time_spent_in_discord_seconds)
	time3 = seconds_converter(users_tot[-3].time_spent_in_discord_seconds)

	message_tot_time = "____ Trogna n??rdar ____\n \
		1. {user_1}: {h1} timmar och {m1} minuter\n\
		2. {user_2}: {h2} timmar och {m2} minuter\n\
		3. {user_3}: {h3} timmar och {m3} minuter\n".format(\
			user_1 = users_tot[-1].user_str, h1 = time1[2], m1 = time1[1],\
			user_2 = users_tot[-2].user_str, h2 = time2[2], m2 = time2[1],\
			user_3 = users_tot[-3].user_str, h3 = time3[2], m3 = time3[1])

	# AVERAGE TIME
	time1 = seconds_converter(users_avg[-1].avg_time_per_session_seconds)
	time2 = seconds_converter(users_avg[-2].avg_time_per_session_seconds)
	time3 = seconds_converter(users_avg[-3].avg_time_per_session_seconds)

	message_avg_time = "____ Fyrkantiga ??gon ____\n \
		1. {user_1}: {h1} timmar och {m1} minuter\n\
		2. {user_2}: {h2} timmar och {m2} minuter\n\
		3. {user_3}: {h3} timmar och {m3} minuter\n".format(\
			user_1 = users_avg[-1].user_str, h1 = time1[2], m1 = time1[1],\
			user_2 = users_avg[-2].user_str, h2 = time2[2], m2 = time2[1],\
			user_3 = users_avg[-3].user_str, h3 = time3[2], m3 = time3[1])

	# STREAM TIME
	time1 = seconds_converter(users_str[-1].time_spent_streaming)
	time2 = seconds_converter(users_str[-2].time_spent_streaming)
	time3 = seconds_converter(users_str[-3].time_spent_streaming)
	
	message_str_time = "____ Streamers ____\n \
		1. {user_1}: {h1} timmar och {m1} minuter\n\
		2. {user_2}: {h2} timmar och {m2} minuter\n\
		3. {user_3}: {h3} timmar och {m3} minuter\n".format(\
			user_1 = users_str[-1].user_str, h1 = time1[2], m1 = time1[1],\
			user_2 = users_str[-2].user_str, h2 = time2[2], m2 = time2[1],\
			user_3 = users_str[-3].user_str, h3 = time3[2], m3 = time3[1])

	# NUM OF AFKS AND BONKS
	message_afk_num = "____ \"BRB runka\" ____\n \
		1. {user_1}: {t1} g??nger\n\
		2. {user_2}: {t2} g??nger\n\
		3. {user_3}: {t3} g??nger\n".format(\
			user_1 = users_afk[-1].user_str, t1 = users_afk[-1].num_of_afk,\
			user_2 = users_afk[-2].user_str, t2 = users_afk[-2].num_of_afk,\
			user_3 = users_afk[-3].user_str, t3 = users_afk[-3].num_of_afk)
			
	message_to_send = message_tot_time + "\n" + message_avg_time + "\n" + message_str_time + "\n" + message_afk_num
	await ctx.send(message_to_send)

async def read_stats():
	

	guild_id = 668194960637558784
	guild = bot.get_guild(guild_id)
	
	with open("stats.txt", 'r') as stat_file:
		contents = stat_file.read().split(',\n')[:-1]
		if len(contents) % 9 != 0:
			log.log("Error when reading stats.txt")

		for i in range(len(contents)//9): #Every MemberStat has 9 attributes

			# Get MemberStat attributes
			discordMemberInstance = await guild.fetch_member(int(contents[9*i]))
			user = MemberStat(discordMemberInstance)
			user.times_joined = int(contents[9*i+1])
			user.time_spent_in_discord_seconds = float(contents[9*i+2])
			user.avg_time_per_session_seconds = float(contents[9*i+3])
			user.num_of_afk = int(contents[9*i+4])
			user.last_join_time = float(contents[9*i+5])
			user.messages_sent = int(contents[9*i+6])
			user.last_stream_time = float(contents[9*i+7])
			user.time_spent_streaming = float(contents[9*i+8])

			user_stats[contents[i]] = user


"""
TODO: implement ability to force a save in order to update from git
"""
async def save_stats():
	while True:
		with open("stats.txt", 'w+') as stat_file:
			for user in user_stats.values():
				stat_file.write(user.get_user_stats_csv())
			log.log("Saved stats to file")

		await asyncio.sleep(900) #sleep for 900s (15 min)




bot.run(TOKEN)
