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
bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.environ['TOKEN']

SFXlst = {"milk" : "https://youtu.be/xfl31la4f2E?t=1", 
		"bonk" :"https://www.youtube.com/watchv=gwxTZaa3NgIab_channel=YerBoiLloris",
		"what" : "https://www.youtube.com/watch?v=pYaX22MTp8gab_channel=MemeSounds"}

bonk_lst = []
knownUserAlias = {}
user_stats = {}

class MemberStat:

	def __init__(self, member, times_joined = 0, time_spent_in_discord = 0.0, num_of_afk = 0, last_join = 0):
		self.times_joined = times_joined
		self.time_spent_in_discord = time_spent_in_discord
		self.num_of_afk = num_of_afk
		self.last_join = last_join
		self.member = member


@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')


# Check if joining user has been bonked since their last connection
# and logs their stats
@bot.event
async def on_voice_state_update(user: discord.Member, before, after):
	# if the coroutine is activated for other reasons than a user moving voice-channel, ignore
	if before.channel == after.channel:
		return

	if before.channel is None:
		print("join")
		if user in bonk_lst:
			bonk(user.Guild.system_channel, user)
		
		join_time = time.time()

		if not user in user_stats:
			print("hej")
			new_user = MemberStat(user, 1, join_time)
			user_stats[user.id] = new_user
			return
		stats = user_stats[user.id]
		stats.times_joined += 1
		stats.last_join = join_time
	
	elif before.channel is not None and after.afk is True:
		pass



@bot.event
async def on_member_remove(user: discord.Member):
	leave_time = time.time()
	stats = user_stats[user.id]
	time_delta = leave_time - stats.last_join
	stats.time_spent_in_discord += time_delta
	print("lämnade")


@bot.event
async def on_member_state_update(before, after):
	print("update")
	user = before
	ctx = user.ctx
	if before.channel is not None:
		stats = user_stats[user.id]
		if before.channel is ctx.Guild.afk_channel:
			print("lämnade afk")
			join_time = time.time()
			stats.last_join = join_time

		elif after.channel is ctx.Guild.afk_channel:
			print("gick afk")
			stats.num_of_afk += 1
			afk_time = time.time()
			time_delta = afk_time - stats.last_join
			stats.time_spent_in_discord += time_delta


@bot.command()
async def test(ctx, arg="ful"):
	await ctx.send(f"näe du är {arg}.")

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



@bot.command()
async def stats(ctx, user: discord.Member):
	"""
	stats = user_stats[user]
	await ctx.send(f"{str(user).split('#')[0]} har varit i denna discord hela {stats.time_spent_in_discord} och gått afk {stats.num_of_afk} gånger")
	"""
	print(user_stats)


bot.run(TOKEN)