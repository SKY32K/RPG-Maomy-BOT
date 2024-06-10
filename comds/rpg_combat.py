import discord
from discord.ext import commands
from discord import app_commands

class Combat(commands.Cog):
    def __init__(self, bot, character_cog):
        self.bot = bot
        self.character_cog = character_cog

    @app_commands.command(name="角色遊戲_角色遊戲戰鬥", description="跟一個人進行RPG戰鬥")
    async def attack(self, interaction, target: discord.Member):
        attacker = self.character_cog.characters.get(interaction.user.id)
        defender = self.character_cog.characters.get(target.id)

        if not attacker or not defender:
            await interaction.response.send_message('攻擊者和被攻擊者都必須有角色。', ephemeral=True)
            return

        # 計算職業和等級加成
        level_multiplier = 1 + (attacker["level"] // 10) * 0.1
        damage = int(attacker["strength"] * attacker["attack"] * level_multiplier)
        defender["hp"] -= damage
        self.character_cog.save_characters()
        await interaction.response.send_message(f'{attacker["name"]} 攻擊了 {defender["name"]}，造成 {damage} 點傷害！', ephemeral=True)

        if defender["hp"] <= 0:
            await interaction.response.send_message(f'{defender["name"]} 被擊敗了！', ephemeral=True)

async def setup(bot):
    character_cog = bot.get_cog('Character')
    await bot.add_cog(Combat(bot, character_cog))
