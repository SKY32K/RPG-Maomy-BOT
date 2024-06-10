import discord
from discord import app_commands
from discord.ext import commands
import random

class Skills(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="角色遊戲_恢復技能", description="法師恢復技能")
    async def heal(self, interaction: discord.Interaction):
        character_cog = self.bot.get_cog('Character')
        user_id = str(interaction.user.id)
        character = character_cog.load_character(user_id)

        if character["role"] != "法師":
            await interaction.response.send_message('只有法師可以使用恢復技能。')
            return

        heal_amount = int(character["intelligence"] * 2)
        character["hp"] += heal_amount
        character_cog.save_character(user_id, character)
        await interaction.response.send_message(f'{character["name"]} 恢復了 {heal_amount} 點HP！')

    @app_commands.command(name="角色遊戲_廚師製造食物", description="廚師製造食物")
    async def cook(self, interaction: discord.Interaction):
        character_cog = self.bot.get_cog('Character')
        user_id = str(interaction.user.id)
        character = character_cog.load_character(user_id)

        if character["role"] != "廚師":
            await interaction.response.send_message('只有廚師可以製造食物。')
            return

        food = {"name": "食物", "hp_increase": 20, "attack_boost": 1.1, "duration": 5}
        character["inventory"].append(food)
        character_cog.save_character(user_id, character)
        await interaction.response.send_message(f'{character["name"]} 製造了一份食物並放入了包包。')

    @app_commands.command(name="角色遊戲_鐵匠製造裝備", description="鐵匠製造裝備")
    @app_commands.describe(level="裝備等級 (1, 2, 3)")
    async def craft(self, interaction: discord.Interaction, level: int):
        character_cog = self.bot.get_cog('Character')
        user_id = str(interaction.user.id)
        character = character_cog.load_character(user_id)

        if character["role"] != "鐵匠":
            await interaction.response.send_message('只有鐵匠可以製造裝備。')
            return

        cost = [50, 100, 200]
        success_rate = [0.6, 0.3, 0.15]
        if level < 1 or level > 3:
            await interaction.response.send_message('裝備等級無效。有效等級為1, 2, 3。')
            return

        if character["level"] >= 10:
            success_rate = [rate * 1.1 for rate in success_rate]
            success_rate = [round(rate, 1) for rate in success_rate]

        if character["tokens"] < cost[level - 1]:
            await interaction.response.send_message('你的代幣不足。')
            return

        character["tokens"] -= cost[level - 1]
        success = random.random() < success_rate[level - 1]

        if success:
            equipment = {"level": level, "defense_boost": 0.05 * level, "attack_boost": 0.05 * level}
            character["inventory"].append(equipment)
            await interaction.response.send_message(f'成功製造了一件{level}級裝備！')
        else:
            await interaction.response.send_message(f'製造{level}級裝備失敗。')

        character_cog.save_character(user_id, character)

async def setup(bot):
    await bot.add_cog(Skills(bot))