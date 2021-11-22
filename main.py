import discord
from discord.ext import commands
import jstrisfunctions
from jstrisfunctions import LiveDateInit
from jstrisfunctions import IndivParameterInit
from jstrisuser import UserIndivGames
from jstrisuser import UserLiveGames
import asyncio
from concurrent.futures import ThreadPoolExecutor

intents = discord.Intents.default()
intents.members = True
description = 'Third party bot to quickly gather Jstris stats on individual players'

bot = commands.Bot(command_prefix='?', description=description, intents=intents, help_command=None)
LOOP = asyncio.get_event_loop()
num_processes = 0


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command()
async def help(ctx):
    await ctx.send("https://docs.google.com/document/d/1D54qjRTNmkOBXcvff1vpiph5E5txnd6J6R2oI9e6ZMM/edit?usp=sharing")


# SINGLE PLAYER COMMANDS

@bot.command()
async def least(ctx, username: str, *args):
    if not await num_processes_init(ctx):
        return None

    my_ps = IndivParameterInit(args)

    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserIndivGames,
                                                username, my_ps.game, my_ps.mode, my_ps.period)
    await num_processes_finish()

    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(searched_games.error_message)
    else:
        a = jstrisfunctions.least_(searched_games.all_stats, my_ps.param)
        await replay_send(ctx, a)


@bot.command()
async def most(ctx, username: str, *args):
    if not await num_processes_init(ctx):
        return None

    my_ps = IndivParameterInit(args)

    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserIndivGames,
                                                username, my_ps.game, my_ps.mode, my_ps.period)
    await num_processes_finish()

    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
    else:
        a = jstrisfunctions.most_(searched_games.all_stats, my_ps.param)
        await replay_send(ctx, a)


@bot.command()
async def average(ctx, username: str, *args):
    if not await num_processes_init(ctx):
        return None

    my_ps = IndivParameterInit(args)

    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserIndivGames,
                                                username, my_ps.game, my_ps.mode, my_ps.period)
    await num_processes_finish()
    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
    else:
        my_average = jstrisfunctions.average_(searched_games.all_stats, my_ps.param)
        await ctx.send(ctx.author.mention)
        await ctx.send(f"Average {my_ps.param} for {username} is: {my_average}")


@bot.command()
async def numgames(ctx, username: str, *args):
    if not await num_processes_init(ctx):
        return None

    my_ps = IndivParameterInit(args)
    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserIndivGames,
                                                username, my_ps.game, my_ps.mode, my_ps.period)
    await num_processes_finish()

    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(searched_games.error_message)
    else:
        a = len(searched_games.all_stats)
        await ctx.send(ctx.author.mention)
        await ctx.send(f"{str(a)} games")


@bot.command()
async def sub300(ctx, username: str, period: str = "alltime"):
    if not await num_processes_init(ctx):
        return None

    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")

    args = (period, '')
    my_ps = IndivParameterInit(args)
    period = my_ps.period
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserIndivGames,
                                                username, "3", "3", period)
    await num_processes_finish()
    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
    else:
        a = jstrisfunctions.sub300(searched_games.all_stats)
        await ctx.send(ctx.author.mention)
        await ctx.send(f"{username} has {a} sub 300s")


# VERSUS COMMANDS

@bot.command()
async def vs(ctx, username: str, offset: int = 10):
    if not await num_processes_init(ctx):
        return None

    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserLiveGames,
                                                username, offset)
    await num_processes_finish()
    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
        return None

    # Calculates averages
    apm_avg = str(jstrisfunctions.live_games_avg(searched_games.all_stats, offset, 'apm'))
    spm_avg = str(jstrisfunctions.live_games_avg(searched_games.all_stats, offset, 'spm'))
    pps_avg = str(jstrisfunctions.live_games_avg(searched_games.all_stats, offset, 'pps'))
    weight_apm = str(round(jstrisfunctions.live_games_weighted_avg(searched_games.all_stats, offset, 'attack') * 60, 2))
    weight_spm = str(round(jstrisfunctions.live_games_weighted_avg(searched_games.all_stats, offset, 'sent') * 60, 2))
    weight_pps = str(round(jstrisfunctions.live_games_weighted_avg(searched_games.all_stats, offset, 'pcs'), 2))
    time_avg = str(jstrisfunctions.live_games_avg(searched_games.all_stats, offset, 'gametime'))
    players_avg = str(jstrisfunctions.live_games_avg(searched_games.all_stats, offset, 'players'))
    pos_avg = str(jstrisfunctions.live_games_avg(searched_games.all_stats, offset, 'pos'))
    won_games = jstrisfunctions.games_won(searched_games.all_stats, offset)

    # Discord formatting
    embed = await embed_init(username)
    embed.add_field(name="**apm:**", value=apm_avg, inline=True)
    embed.add_field(name="**spm:**", value=spm_avg, inline=True)
    embed.add_field(name="**pps:**", value=pps_avg, inline=True)
    embed.add_field(name="**apm (weighted):**", value=weight_apm, inline=True)
    embed.add_field(name="**spm (weighted):**", value=weight_spm, inline=True)
    embed.add_field(name="**pps (weighted):**", value=weight_pps, inline=True)
    embed.add_field(name="**time (seconds):**", value=time_avg, inline=True)
    embed.add_field(name="**final position:**", value=pos_avg, inline=True)
    embed.add_field(name="**players:**", value=players_avg, inline=True)
    embed.add_field(name="**games won:**", value=f"{won_games}  ({won_games/offset*100:.2f}%)", inline=False)
    embed.add_field(name="**number of games:**", value=str(offset), inline=False)
    embed.set_footer(text='All of these values are averages. Weighted means weighted by time, not game.')
    await ctx.send(ctx.author.mention)
    await ctx.send(embed=embed)


@bot.command()
async def allmatchups(ctx, username: str, first_date: str = "1000 months", last_date: str = "0 days"):
    date_init = LiveDateInit(first_date, last_date)
    if date_init.has_error:
        await ctx.send(date_init.error_message)
        return 0

    first_date = date_init.first
    last_date = date_init.last

    if not await num_processes_init(ctx):
        return None

    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserLiveGames,
                                                username, 1000000000, first_date, last_date)
    await num_processes_finish()
    await init_message.delete()
    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
        return None
    list_of_opponents = jstrisfunctions.opponents_matchups(searched_games.all_stats)

    # Discord formatting stuff

    embed = await embed_init(username)

    c = 0
    for key in list_of_opponents:
        if key is None:
            continue
        winrate = list_of_opponents[key]["won"] / list_of_opponents[key]["games"] * 100
        won_games = list_of_opponents[key]['won']
        embed.add_field(name='**opponent:**', value=f"{c+1}. {key}", inline=True)
        embed.add_field(name='**games won (by user):**', value=f"{won_games}  ({winrate:.2f}%)", inline=True)
        embed.add_field(name='**total games:**', value=list_of_opponents[key]["games"], inline=True)
        c += 1
        if c >= 8:
            break
    embed.set_footer(text='Only the top 8 players with most played games are shown here for technical reasons. '
                          'For individual match ups, try using ?indivmatchup instead. Also, Jstris will delete replays'
                          'over time, and they will not be counted here.')

    await ctx.send(ctx.author.mention)
    await ctx.send(embed=embed)


@bot.command()
async def vsmatchup(ctx, username: str, opponent: str, first_date: str = "1000 months", last_date: str = "0 days"):
    username = username.lower()
    opponent = opponent.lower()
    date_init = LiveDateInit(first_date, last_date)
    if date_init.has_error:
        await ctx.send(date_init.error_message)
        return 0

    first_date = date_init.first
    last_date = date_init.last

    if not await num_processes_init(ctx):
        return None
    init_message = await ctx.send(f"Searching {username}'s games now. This can take a while.")

    # Username's games
    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserLiveGames,
                                                username, 10000000000, first_date, last_date)

    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
        return None
    list_of_opponents = jstrisfunctions.opponents_matchups(searched_games.all_stats)
    embed1 = await vs_matchup_embed(ctx, username, opponent, list_of_opponents)

    # Opponent's games
    opp_first_date = list_of_opponents[opponent]["min_time"]
    opp_last_date = list_of_opponents[opponent]["max_time"]
    print(opp_first_date, opp_last_date)

    searched_games = await LOOP.run_in_executor(ThreadPoolExecutor(),
                                                UserLiveGames,
                                                opponent, 10000000, opp_first_date, opp_last_date)
    # print(searched_games.all_stats)
    if searched_games.has_error:
        await ctx.send(ctx.author.mention)
        await ctx.send(searched_games.error_message)
        return None
    list_of_opponents = jstrisfunctions.opponents_matchups(searched_games.all_stats)
    embed2 = await vs_matchup_embed(ctx, opponent, username, list_of_opponents)

    # Finalizing

    await num_processes_finish()
    await init_message.delete()

    await ctx.send(ctx.author.mention)
    await ctx.send(embed=embed1)
    await ctx.send(embed=embed2)


# OTHER METHODS

async def replay_send(ctx, my_ps: dict) -> None:
    embed = await embed_init(my_ps['username'])

    for i in my_ps:
        if i not in ("username", 'replay'):
            embed.add_field(name=f"**{i}:**", value=my_ps[i], inline=False)
    if my_ps["replay"] != "- ":
        embed.add_field(name="**replay:**", value=my_ps['replay'], inline=False)
    else:
        embed.add_field(name="**replay:**", value="replay not available", inline=False)
    embed.set_footer(text='Have any suggestions? Please message Truebulge#0358 on Discord!')
    await ctx.send(ctx.author.mention)
    await ctx.send(embed=embed)


async def embed_init(username: str) -> discord.Embed:
    embed = discord.Embed(
        title=username,
        url=f"https://jstris.jezevec10.com/u/{username}",
        color=discord.Colour.red())
    embed.set_author(name="BadgerBot")
    embed.set_thumbnail(url="https://i.imgur.com/WDUv9f0.png")
    return embed


async def vs_matchup_embed(ctx, username: str, opponent: str, list_of_opponents: dict):
    embed = await embed_init(username)

    if opponent in list_of_opponents:
        winrate = list_of_opponents[opponent]["won"] / list_of_opponents[opponent]["games"] * 100
        won_games = list_of_opponents[opponent]['won']
        has_opponent = True
        embed.add_field(name='**opponent:**', value=opponent, inline=True)
        embed.add_field(name='**games won:**', value=f"{won_games}  ({winrate:.2f}%)", inline=True)
        embed.add_field(name='**total games:**', value=list_of_opponents[opponent]["games"], inline=True)
        embed.add_field(name='**apm:**', value=list_of_opponents[opponent]["apm"], inline=True)
        embed.add_field(name='**spm:**', value=list_of_opponents[opponent]["spm"], inline=True)
        embed.add_field(name='**pps:**', value=list_of_opponents[opponent]["pps"], inline=True)
        embed.add_field(name='**apm (weighted):**', value=list_of_opponents[opponent]["wapm"], inline=True)
        embed.add_field(name='**spm (weighted):**', value=list_of_opponents[opponent]["wspm"], inline=True)
        embed.add_field(name='**pps (weighted):**', value=list_of_opponents[opponent]["wpps"], inline=True)
        embed.set_footer(text='All stats here are for the player, not the opponent. To find the opponents stats, '
                              'simply call this command again in reverse. Also, Jstris will delete replays over time, '
                              'and they will not be counted here. Weighted means weighted by time, not game.')
    else:
        has_opponent = False

    if not has_opponent:
        await ctx.send(ctx.author.mention)
        await ctx.send(f"No found games of {username} vs {opponent}.")
        return None

    return embed


async def num_processes_init(ctx) -> bool:
    global num_processes
    num_processes += 1
    if num_processes > 5:
        num_processes -= 1
        await ctx.send(ctx.author.mention)
        await ctx.send("Sorry, currently busy handling other requests. Please try again in a few minutes.")
        return False
    return True


async def num_processes_finish():
    global num_processes
    num_processes -= 1

if __name__ == "__main__":

    # Token

    bot.run('OTA2NzEyOTE0Njc1Nzg5ODU1.YYcoNA.K2uerr4Q3kwY3Rj3RnLWTemZNbQ')
