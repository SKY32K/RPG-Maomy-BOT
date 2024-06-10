import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

class rpg_Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="角色遊戲_給予角色遊戲代幣給成員", description="擁有者|給予成員代幣")
    @commands.is_owner()
    async def addtokens(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user_id = str(member.id)
        character_cog = self.bot.get_cog('Character')
        character = character_cog.load_character(user_id)

        if not character:
            await interaction.response.send_message(f'{member.display_name} 還沒有角色。', ephemeral=True)
            return

        character["tokens"] += amount
        character_cog.save_character(user_id, character)
        await interaction.response.send_message(f'已給予 {member.display_name} {amount} 代幣。', ephemeral=True)

    @app_commands.command(name="角色遊戲_移除成員角色遊戲代幣", description="擁有者|移除成員的代幣")
    @commands.is_owner()
    async def remtokens(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user_id = str(member.id)
        character_cog = self.bot.get_cog('Character')
        character = character_cog.load_character(user_id)

        if not character:
            await interaction.response.send_message(f'{member.display_name} 還沒有角色。', ephemeral=True)
            return

        character["tokens"] -= amount
        character_cog.save_character(user_id, character)
        await interaction.response.send_message(f'已移除 {amount} 代幣從 {member.display_name}。', ephemeral=True)

    @app_commands.command(name="角色遊戲_轉移物品給他人", description="轉移物品給成員")
    async def transfer(self, interaction: discord.Interaction, member: discord.Member, item_name: str):
        user_id = str(interaction.user.id)
        recipient_id = str(member.id)
        character_cog = self.bot.get_cog('Character')
        sender = character_cog.load_character(user_id)
        recipient = character_cog.load_character(recipient_id)

        if not recipient:
            await interaction.response.send_message(f'{member.display_name} 還沒有角色。', ephemeral=True)
            return

        item = next((i for i in sender["inventory"] if i["name"] == item_name), None)
        if not item:
            await interaction.response.send_message('你沒有這個物品。', ephemeral=True)
            return

        view = View()
        view.add_item(TransferButton(self, item, member))
        await interaction.response.send_message('確認轉送物品？', view=view, ephemeral=True)

class TransferButton(Button):
    def __init__(self, cog, item, recipient):
        self.cog = cog
        self.item = item
        self.recipient = recipient
        super().__init__(label=f'轉送 {item["name"]} 給 {recipient.display_name}', style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: discord.Interaction):
        sender_id = str(interaction.user.id)
        recipient_id = str(self.recipient.id)
        character_cog = self.cog.bot.get_cog('Character')
        sender = character_cog.load_character(sender_id)
        recipient = character_cog.load_character(recipient_id)

        if not recipient:
            await interaction.response.send_message(f'{self.recipient.display_name} 還沒有角色。', ephemeral=True)
            return

        if self.item not in sender["inventory"]:
            await interaction.response.send_message('你沒有這個物品。', ephemeral=True)
            return

        sender["inventory"].remove(self.item)
        recipient["inventory"].append(self.item)
        character_cog.save_character(sender_id, sender)
        character_cog.save_character(recipient_id, recipient)
        await interaction.response.send_message(f'成功轉送 {self.item["name"]} 給 {self.recipient.display_name}！', ephemeral=True)

async def setup(bot):
    await bot.add_cog(rpg_Economy(bot))