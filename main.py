import os
import time
import datetime
import asyncio
import interactions
import requests
import pickle
from keep_alive import keep_alive
from leaderboard_template import template
from bidict import UniqueBidict

# Settings
mock = False

# Bot
bot = interactions.Client(token=os.environ['BOT_TOKEN'],
                          default_scope=1033109279399485560)
completion_role = 1047995823981604884

# API Data
last_ping_time = 0
api_url = "https://adventofcode.com/2022/leaderboard/private/view/758050.json"
mock_api_url = "https://run.mocky.io/v3/2c91d07e-03c9-4ab2-8a7b-8ffc77f324e5"
api_cookie = {"session": os.environ['AOC_COOKIE']}
if mock:
    api_url = mock_api_url

# Storage
leaderboard_data = {}


def save_data(account_data):
    with open("accounts.dat", "wb") as f:
        pickle.dump(account_data._dict, f)


def load_data():
    try:
        with open("accounts.dat", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}


account_data = UniqueBidict(load_data())


# Update Command
@bot.command(name="update",
             description="Forces an update of the bot's leaderboard now.")
async def update(ctx: interactions.CommandContext):
    if not await _update():
        await ctx.send(
            "A request can only be sent to the API every 15 minutes!",
            ephemeral=True)
    else:
        await ctx.send("Successfully updated leaderboard data!")


# Link Command
@bot.command(name="link",
             description="Links your discord account to your AoC username.",
             options=[
                 interactions.Option(
                     name="username",
                     description="Your AoC username on the leaderboard",
                     type=interactions.OptionType.STRING,
                     required=True)
             ])
async def link(ctx: interactions.CommandContext, username: str):
    account_data[str(ctx.author.user.id)] = username
    save_data(account_data)
    await ctx.send("Linked successfully!", ephemeral=True)


# Leaderboard Command
@bot.command(name="leaderboard", description="Shows the current leaderboard")
async def leaderboard(ctx: interactions.CommandContext):
    if leaderboard_data == {}:
        await ctx.send(
            "Please run /update first to update the leaderboard internally",
            ephemeral=True)
        return

    t = interactions.Embed(**template)
    for id, member in leaderboard_data["members"].items():
        row = ["✧"] * 25
        for dayno, day in member["completion_day_level"].items():
            row[int(dayno) - 1] = ("★" if ("2" in day.keys()) else "☆")

        name = member['name']
        if name in account_data.values():
            name = (await
                    (await
                     ctx.get_guild()).get_member(account_data[:name])).mention
        t.add_field("\u200b", f"**{name}**\n" + ''.join(row))

    await ctx.send(embeds=t)


async def _update():
    global last_ping_time, leaderboard_data
    if time.time() - last_ping_time < 15 * 60:
        return False
    last_ping_time = time.time()

    leaderboard_data = requests.get(api_url, cookies=api_cookie).json()

    for id, member in leaderboard_data["members"].items():
        if str(datetime.datetime.today().day
               ) in member["completion_day_level"].keys():
            name = member['name']
            if name in account_data.values():
                for guild in bot.guilds:
                    await guild.add_member_role(completion_role, account_data[:name])

    return True


async def periodic_update():
    while True:
        print("Updating automatically...")
        print(f"Done with result {await _update()}")
        await asyncio.sleep(45 * 60)


async def periodic_clear_roles():
    while True:
        await asyncio.sleep((datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1), datetime.time.min) -
         datetime.datetime.now()).seconds)

        
        for guild in bot.guilds:
            for member in account_data.keys():
                await guild.remove_member_role(completion_role, member)


asyncio.get_event_loop().create_task(periodic_update())
asyncio.get_event_loop().create_task(periodic_clear_roles())

# Run Bot
keep_alive()
bot.start()
