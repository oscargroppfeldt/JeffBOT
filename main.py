import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = os.environ['TOKEN']

bonk_lst = []
knownUserAlias = {}

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')

# Check if joining user has been bonked since their last connection
@bot.event
async def on_member_join(ctx, user: discord.Member):
	if user in bonk_lst:
		bonk(ctx, user)

@bot.command()
async def test(ctx, arg="ful"):
	await ctx.send(f"näe du är {arg}.")



# Moves the given user to the afk-channel
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
	if user.id == 909533326199623781:
		await ctx.send(f"Du bör passa dig jävligt noga nu {ctx.message.author}.")


	voice_state = user.voice
	try:
		if voice_state is None:
			await ctx.send(str(user).split('#')[0] + " är ju inte här, bonkar honom när han kommer tillbaka.\n ;)")
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



# Adds an alias for user
@bot.command()
async def addAlias(ctx, user: discord.Member, arg: str):
	knownUserAlias[arg] = user
	await ctx.send(f"HAHAHA kallar ni {str(user).split('#')[0]} för {arg}?\nAja okej då...")
	

bot.run(TOKEN)