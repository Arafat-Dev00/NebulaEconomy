import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)



token = os.getenv("token")




user_balances = {}
user_inventories = {}
items = {'apple': 10, 'banana': 15, 'carrot': 5}
pending_trades = {}
last_claimed = {}
user_jobs = {}
investments = {}
achievements = {}
last_work_time = {}

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    await bot.tree.sync()

def create_embed(title, description):
    embed = discord.Embed(title=title, description=description, color=discord.Color.purple())
    return embed

@bot.hybrid_command(name='balance', description='Check your current balance.')
async def balance(ctx):
    user_id = str(ctx.author.id)
    balance = user_balances.get(user_id, 0)
    embed = create_embed('Balance', f'{ctx.author.mention}, your balance is {balance} coins.')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='earn', description='Earn a specified amount of coins.')
async def earn(ctx, amount: int):
    user_id = str(ctx.author.id)
    user_balances[user_id] = user_balances.get(user_id, 0) + amount
    check_and_grant_achievement(ctx.author, user_id)
    embed = create_embed('Earned Coins', f'{ctx.author.mention}, you earned {amount} coins! Your new balance is {user_balances[user_id]} coins.')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='buy', description='Purchase items from the shop.')
async def buy(ctx, item: str, quantity: int):
    user_id = str(ctx.author.id)
    if item not in items:
        embed = create_embed('Shop', f'{ctx.author.mention}, {item} is not available in the shop.')
        await ctx.send(embed=embed)
        return
    
    cost = items[item] * quantity
    if user_balances.get(user_id, 0) < cost:
        embed = create_embed('Shop', f'{ctx.author.mention}, you do not have enough coins.')
        await ctx.send(embed=embed)
        return
    
    user_balances[user_id] -= cost
    check_and_grant_achievement(ctx.author, user_id)
    if user_id in user_inventories:
        if item in user_inventories[user_id]:
            user_inventories[user_id][item] += quantity
        else:
            user_inventories[user_id][item] = quantity
    else:
        user_inventories[user_id] = {item: quantity}
    
    embed = create_embed('Shop', f'{ctx.author.mention}, you bought {quantity} {item}(s).')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='inventory', description='View your inventory.')
async def inventory(ctx):
    user_id = str(ctx.author.id)
    inventory = user_inventories.get(user_id, {})
    inventory_list = '\n'.join([f'{item}: {quantity}' for item, quantity in inventory.items()])
    embed = create_embed('Inventory', f'{ctx.author.mention}, your inventory:\n{inventory_list}')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='trade', description='Trade items with other users.')
async def trade(ctx, target: discord.Member, item: str, quantity: int):
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    if item not in user_inventories.get(user_id, {}):
        embed = create_embed('Trade', f'{ctx.author.mention}, you do not have {quantity} {item}(s) to trade.')
        await ctx.send(embed=embed)
        return
    
    pending_trades[user_id] = {'target': target_id, 'item': item, 'quantity': quantity}
    embed = create_embed('Trade', f'{ctx.author.mention}, trade request sent to {target.mention}.')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='accept_trade', description='Accept a pending trade request.')
async def accept_trade(ctx):
    user_id = str(ctx.author.id)
    trade = next((trade for trade in pending_trades.values() if trade['target'] == user_id), None)
    if not trade:
        embed = create_embed('Trade', f'{ctx.author.mention}, no trade request found.')
        await ctx.send(embed=embed)
        return
    
    trader_id = next(user for user, trade in pending_trades.items() if trade['target'] == user_id)
    item = trade['item']
    quantity = trade['quantity']
    
    user_inventories[trader_id][item] -= quantity
    if trader_id not in user_inventories:
        user_inventories[trader_id] = {}
    if item in user_inventories[user_id]:
        user_inventories[user_id][item] += quantity
    else:
        user_inventories[user_id][item] = quantity

    del pending_trades[trader_id]
    embed = create_embed('Trade', f'{ctx.author.mention}, trade accepted. You received {quantity} {item}(s) from {bot.get_user(int(trader_id)).mention}.')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='daily', description='Claim your daily reward.')
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.now()
    if user_id in last_claimed:
        last_time = last_claimed[user_id]
        if now - last_time < timedelta(days=1):
            embed = create_embed('Daily Reward', f'{ctx.author.mention}, you can only claim your daily reward once every 24 hours.')
            await ctx.send(embed=embed)
            return
    
    last_claimed[user_id] = now
    reward = 100
    user_balances[user_id] = user_balances.get(user_id, 0) + reward
    check_and_grant_achievement(ctx.author, user_id)
    embed = create_embed('Daily Reward', f'{ctx.author.mention}, you claimed your daily reward of {reward} coins.')
    await ctx.send(embed=embed)


@bot.hybrid_command(name='leaderboard', description='View the top users by balance.')
async def leaderboard(ctx):
    sorted_users = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)
    leaderboard = '\n'.join([f'<@{user_id}>: {balance} coins' for user_id, balance in sorted_users[:10]])
    embed = create_embed('Leaderboard', f'**Leaderboard**\n{leaderboard}')
    await ctx.send(embed=embed)

jobs = {
    'fisherman': {'payout': random.randint(100, 200), 'cooldown': timedelta(minutes=30)},
    'programmer': {'payout': random.randint(150, 300), 'cooldown': timedelta(minutes=30)},
    'artist': {'payout': random.randint(200, 350), 'cooldown': timedelta(minutes=30)},
    'musician': {'payout': random.randint(250, 400), 'cooldown': timedelta(minutes=30)},
    'delivery_driver': {'payout': random.randint(300, 450), 'cooldown': timedelta(minutes=30)},
    'doctor': {'payout': random.randint(350, 500), 'cooldown': timedelta(minutes=30)},
    'teacher': {'payout': random.randint(400, 550), 'cooldown': timedelta(minutes=30)},
    'chef': {'payout': random.randint(450, 600), 'cooldown': timedelta(minutes=30)},
    'lawyer': {'payout': random.randint(500, 650), 'cooldown': timedelta(minutes=30)},
    'pilot': {'payout': random.randint(550, 700), 'cooldown': timedelta(minutes=30)},
    'engineer': {'payout': random.randint(600, 750), 'cooldown': timedelta(minutes=30)},
}

@bot.hybrid_command(name='job', description='Choose a job and earn income.')
async def job(ctx, job_name: str = None):
    if job_name is None:
        embed = create_embed('Available Jobs', '\n'.join(jobs.keys()))
        await ctx.send(embed=embed)
        return

    user_id = str(ctx.author.id)
    if user_id in last_work_time:
        last_work = last_work_time[user_id]
        time_since_last_work = datetime.now() - last_work
        if time_since_last_work < timedelta(minutes=30):
            remaining_time = timedelta(minutes=30) - time_since_last_work
            embed = create_embed('Job', f'{ctx.author.mention}, you can only work once every 30 minutes. Please wait for {remaining_time}.')
            await ctx.send(embed=embed)
            return
    
    if job_name.lower() not in jobs:
        embed = create_embed('Job', f'{ctx.author.mention}, that job does not exist.')
        await ctx.send(embed=embed)
        return

    job_details = jobs[job_name.lower()]
    payout = job_details['payout']
    
    user_balances[user_id] = user_balances.get(user_id, 0) + payout
    last_work_time[user_id] = datetime.now()
    check_and_grant_achievement(ctx.author, user_id)
    embed = create_embed('Job', f'{ctx.author.mention}, you worked as a {job_name} and earned {payout} coins!')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='collect', description='Collect income every 30 minutes.')
async def collect(ctx):
    user_id = str(ctx.author.id)
    if user_id in last_work_time:
        last_work = last_work_time[user_id]
        time_since_last_work = datetime.now() - last_work
        if time_since_last_work < timedelta(minutes=30):
            remaining_time = timedelta(minutes=30) - time_since_last_work
            embed = create_embed('Collect Income', f'{ctx.author.mention}, you can only collect income once every 30 minutes. Please wait for {remaining_time}.')
            await ctx.send(embed=embed)
            return

    total_payout = 0
    for job_name, job_details in jobs.items():
        job_payout = job_details['payout']
        total_payout += job_payout
        user_balances[user_id] = user_balances.get(user_id, 0) + job_payout
    
    last_work_time[user_id] = datetime.now()
    check_and_grant_achievement(ctx.author, user_id)
    embed = create_embed('Collect Income', f'{ctx.author.mention}, you collected your income of {total_payout} coins!')
    await ctx.send(embed=embed)
    
@bot.hybrid_command(name='invest', description='Invest a certain amount of coins.')
async def invest(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0:
        embed = create_embed('Invest', f'{ctx.author.mention}, please enter a valid amount to invest.')
        await ctx.send(embed=embed)
        return
    
    if user_balances.get(user_id, 0) < amount:
        embed = create_embed('Invest', f'{ctx.author.mention}, you do not have enough coins to invest that amount.')
        await ctx.send(embed=embed)
        return

    user_balances[user_id] -= amount
    investments[user_id] = investments.get(user_id, 0) + amount
    embed = create_embed('Invest', f'{ctx.author.mention}, you have invested {amount} coins.')
    await ctx.send(embed=embed)

    async def investment_returns():
        await bot.wait_until_ready()
        while not bot.is_closed():
            for user_id, amount in investments.items():
                returns = amount * 0.05
                user_balances[user_id] += returns
                investments[user_id] -= returns
            await asyncio.sleep(300)  # 5 minutes interval (300 seconds)

    bot.loop.create_task(investment_returns())
    async def investment_returns():
        await bot.wait_until_ready()
        while not bot.is_closed():
            for user_id, amount in investments.items():
                returns = amount * 0.05
                user_balances[user_id] += returns
                investments[user_id] -= returns
            await asyncio.sleep(300)  # 5 minutes interval (300 seconds)

    async def main():
        bot.loop.create_task(investment_returns())
        await bot.start(token)

    if __name__ == "__main__":
        asyncio.run(main())

@bot.hybrid_command(name='achievements', description='View your unlocked achievements.')
async def achievements(ctx):
    user_id = str(ctx.author.id)
    user_achievements = achievements.get(user_id, 'No achievements yet.')
    embed = create_embed('Achievements', f'{ctx.author.mention}, your achievements: {user_achievements}')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='mini_game', description='Play a mini-game to earn coins.')
async def mini_game(ctx):
    user_id = str(ctx.author.id)
    outcome = random.choice(['win', 'lose'])
    reward = random.randint(50, 200) if outcome == 'win' else 0
    user_balances[user_id] = user_balances.get(user_id, 0) + reward
    embed = create_embed('Mini-Game', f'{ctx.author.mention}, you played a mini-game and {outcome}! You earned {reward} coins.')
    await ctx.send(embed=embed)
    
@bot.hybrid_command(name='bot_help', description='Show available commands and their descriptions.')
async def bot_help(ctx):
    command_list = []
    for command in bot.commands:
        command_list.append(f'**{command.name}**: {command.description}')
    embed = discord.Embed(title='Command Help', description='\n'.join(command_list), color=discord.Color.blue())
    await ctx.send(embed=embed)

    

@bot.hybrid_command(name='coin_flip', description='Play a game of coin flip to earn coins.')
async def coin_flip(ctx):
    user_id = str(ctx.author.id)
    outcome = random.choice(['heads', 'tails'])
    amount = random.randint(50, 200)
    user_balances[user_id] = user_balances.get(user_id, 0) + amount
    embed = create_embed('Coin Flip', f'{ctx.author.mention}, you flipped a coin and it landed on {outcome}! You earned {amount} coins.')
    await ctx.send(embed=embed)


@bot.hybrid_command(name='blackjack', description='Play a game of blackjack to earn coins.')
async def blackjack(ctx):
    user_id = str(ctx.author.id)
    outcome = random.choice(['win', 'lose'])
    amount = random.randint(100, 300) if outcome == 'win' else 0
    user_balances[user_id] = user_balances.get(user_id, 0) + amount
    embed = create_embed('Blackjack', f'{ctx.author.mention}, you played a game of blackjack and {outcome}! You earned {amount} coins.')
    await ctx.send(embed=embed)

@bot.hybrid_command(name='achievements', description='View your unlocked achievements.')
async def achievements(ctx):
    user_id = str(ctx.author.id)
    user_achievements = achievements.get(user_id, 'No achievements yet.')
    embed = create_embed('Achievements', f'{ctx.author.mention}, your achievements: {user_achievements}')
    await ctx.send(embed=embed)


# Define the role ID for "The Richest"
THE_RICHEST_ROLE_ID = 1247177712309764167
  # Replace with your actual role ID

def check_and_grant_achievement(user, user_id):
    if user_balances.get(user_id, 0) >= 30000 and user_id not in achievements:
        achievements[user_id] = "The Richest"
        role = discord.utils.get(user.guild.roles, id=THE_RICHEST_ROLE_ID)
        asyncio.run_coroutine_threadsafe(user.add_roles(role), bot.loop)

def create_embed(title, description):
    embed = discord.Embed(title=title, description=description, color=discord.Color.purple())
    return embed

    


bot.run(token)
