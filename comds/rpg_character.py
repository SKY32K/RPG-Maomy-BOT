import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import datetime

class Character(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.characters_dir = './date/characters'
        if not os.path.exists(self.characters_dir):
            os.makedirs(self.characters_dir)
        self.restore_hp.start()

    def load_character(self, user_id):
        character_file = os.path.join(self.characters_dir, f'{user_id}.json')
        if os.path.exists(character_file):
            with open(character_file, 'r') as f:
                return json.load(f)
        return None

    def save_character(self, user_id, data):
        character_file = os.path.join(self.characters_dir, f'{user_id}.json')
        with open(character_file, 'w') as f:
            json.dump(data, f, indent=4)

    def get_base_stats(self, role):
        base_stats = {
            "法師": {"level": 1, "hp": 70, "max_hp": 70, "mp": 120, "strength": 5, "intelligence": 20, "defense": 1.05, "attack": 1.0, "tokens": 1000, "inventory": [], "banned": False},
            "戰士": {"level": 1, "hp": 120, "max_hp": 120, "mp": 50, "strength": 20, "intelligence": 5, "defense": 1.1, "attack": 1.05, "tokens": 1000, "inventory": [], "banned": False},
            "射箭手": {"level": 1, "hp": 90, "max_hp": 90, "mp": 60, "strength": 15, "intelligence": 10, "defense": 1.0, "attack": 1.15, "tokens": 1000, "inventory": [], "banned": False},
            "鐵匠": {"level": 1, "hp": 100, "max_hp": 100, "mp": 40, "strength": 25, "intelligence": 10, "defense": 1.0, "attack": 1.0, "tokens": 1000, "inventory": [], "banned": False},
            "廚師": {"level": 1, "hp": 80, "max_hp": 80, "mp": 70, "strength": 10, "intelligence": 15, "defense": 1.0, "attack": 1.0, "tokens": 1000, "inventory": [], "banned": False}
        }
        return base_stats.get(role, {})

    def level_up(self, character):
        self.ensure_character_keys(character)  # 确保角色有所有必要的键
        character['level'] += 1
        if character['max_hp'] < 300:
            character['max_hp'] = min(character['max_hp'] + 10, 300)  # 每升一级增加10点最大HP，但不超过300
        character['hp'] = character['max_hp']  # 升级时恢复满血
        return character
    
    @tasks.loop(hours=24)
    async def restore_hp(self):
        for filename in os.listdir(self.characters_dir):
            if filename.endswith('.json'):
                user_id = int(filename.split('.')[0])
                character = self.load_character(user_id)
                if character and 'hp' in character and 'max_hp' in character:
                    character['hp'] = character['max_hp']
                    self.save_character(user_id, character)

    @tasks.loop(hours=24)
    async def restore_hp(self):
        for filename in os.listdir(self.characters_dir):
            if filename.endswith('.json'):
                user_id = int(filename.split('.')[0])
                character = self.load_character(user_id)
                if character and 'hp' in character and 'max_hp' in character:
                    character['hp'] = character['max_hp']
                    self.save_character(user_id, character)

    @restore_hp.before_loop
    async def before_restore_hp(self):
        await self.bot.wait_until_ready()
    
    @app_commands.command(name="角色遊戲_創建屬於自己的角色", description="創建一個新角色")
    @app_commands.choices(role=[
        app_commands.Choice(name="法師", value="法師"),
        app_commands.Choice(name="戰士", value="戰士"),
        app_commands.Choice(name="射箭手", value="射箭手"),
        app_commands.Choice(name="鐵匠", value="鐵匠"),
        app_commands.Choice(name="廚師", value="廚師"),
    ])
    async def create_character(self, interaction: discord.Interaction, name: str, role: app_commands.Choice[str]):
        user_id = str(interaction.user.id)
        
        # 加载现有角色
        character = self.load_character(user_id)
        
        if character:
            await interaction.response.send_message(f'你已經有一個名為 {character["name"]} 的角色。')
            return
        
        # 获取角色的基本属性
        base_stats = self.get_base_stats(role.value)
        
        # 创建新角色
        character = {
            "name": name,
            "role": role.value,
            "hp": base_stats["hp"],
            "mp": base_stats["mp"],
            "attack": base_stats["attack"],
            "defense": base_stats["defense"],
            "speed": base_stats["speed"],
            "skills": base_stats["skills"],
            "inventory": base_stats["inventory"],
            "banned": False,
            "level": 1,
            "experience": 0,
            "tokens": 1000
        }
        
        # 保存新角色
        self.save_character(user_id, character)
        
        await interaction.response.send_message(f'角色 {name} ({role.value}) 已創建!')
        
    @app_commands.command(name="角色遊戲_查看自己的角色", description="查看你的角色")
    async def my_character(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        character = self.load_character(user_id)
        if character:
            embed = discord.Embed(
                title=f"你的角色情況",
                description=f'Name: {character["name"]}, \nRole: {character["role"]}, \nLevel: {character["level"]}, \nHP: {character["hp"]}, \nMP: {character["mp"]}, \nStrength: {character["strength"]}, \nIntelligence: {character["intelligence"]}, \nDefense: {character["defense"]}, \nAttack: {character["attack"]}, \nTokens: {character["tokens"]}, \nBanned: {character["banned"]}',
                url="https://0.0.0.0",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now(),
            )  # 获取目标频道对象
            embed.set_author(name=f"{interaction.user.name}角色情況", icon_url="https://cdn.discordapp.com/attachments/1236308387046752367/1236992202987536404/panorama_5.png?ex=663a0643&is=6638b4c3&hm=31a03b3847d365f5e33eec105f8847b16f82a0ed8cf90058d400f8d8c3447207&")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message('你還沒有角色。')

    @app_commands.command(name="角色遊戲_ban", description="禁止一個用戶使用RPG指令")
    @commands.is_owner()
    async def ban(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(member.id)
        character = self.load_character(user_id)
        if character:
            character["banned"] = True
            self.save_character(user_id, character)
            await interaction.response.send_message(f'{character["name"]} 已被禁止使用RPG指令。')
        else:
            await interaction.response.send_message('該用戶還沒有角色。')

    @app_commands.command(name="角色遊戲_unban", description="解除禁止一個用戶使用RPG指令")
    @commands.is_owner()
    async def unban(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(member.id)
        character = self.load_character(user_id)
        if character:
            character["banned"] = False
            self.save_character(user_id, character)
            await interaction.response.send_message(f'{character["name"]} 已被解除禁止使用RPG指令。')
        else:
            await interaction.response.send_message('該用戶還沒有角色。')

    
async def setup(bot):
    await bot.add_cog(Character(bot))