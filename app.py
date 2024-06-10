import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json 
import os
import datetime

bot = commands.Bot(command_prefix="m-", intents=discord.Intents.all(), owner_id=1010166521424781342)

def read_config_data():
    with open('./date/token.json', 'r', encoding='utf8') as file:
        config = json.load(file)
    return config

# 读取配置文件
config = read_config_data()
token = config['token']

async def load_extensions():
    for CogFile in os.listdir('comds'):
        if CogFile.endswith('.py'):
           await bot.load_extension(f'comds.{CogFile[:-3]}')
           print(f"已載入RPG文件 {CogFile}")

@bot.event
async def on_ready():
    await load_extensions()
    slash = await bot.tree.sync()
    print(f'登入 RPG BOT {bot.user.name}')
    print(f'BOT 加載 {len(slash)} 個指令')
    print(f'BOT build:v1.0')
    print(f'同步成功') 

    

async def main():
    async with bot:
        await load_extensions()

bot.run(token)