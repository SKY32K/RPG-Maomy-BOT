import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

class rpg_Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop_file = './date/rpg/shop_inventory.json'
        self.shop_data = self.load_shop_data()
        self.reset_shop_inventory.start()

    def load_shop_data(self):
        if os.path.exists(self.shop_file):
            with open(self.shop_file, 'r') as f:
                return json.load(f)
        return {
            "food": {"price": 100, "stock": 1000, "max_stock": 1000},
            "potions": {
                "attack_10": {"price": 150, "stock": 100, "max_stock": 100},
                "attack_30": {"price": 1000, "stock": 100, "max_stock": 100}
            },
            "equipment": {
                "level_1": {"price": 300, "stock": 30, "max_stock": 30},
                "level_2": {"price": 400, "stock": 10, "max_stock": 10},
                "level_3": {"price": 1000, "stock": 1, "max_stock": 1}
            }
        }

    def save_shop_data(self):
        with open(self.shop_file, 'w') as f:
            json.dump(self.shop_data, f, indent=4)

    @tasks.loop(hours=24)
    async def reset_shop_inventory(self):
        self.shop_data["food"]["stock"] = self.shop_data["food"]["max_stock"]
        for potion in self.shop_data["potions"].values():
            potion["stock"] = potion["max_stock"]
        for equip in self.shop_data["equipment"].values():
            equip["stock"] = equip["max_stock"]
        self.save_shop_data()

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.update_channel_id)
        if channel:
            async for message in channel.history(limit=100):
                if message.author == self.bot.user and message.embeds and message.embeds[0].title == "商店商品庫存更新":
                    self.shop_status_message_id = message.id
                    break
        self.reset_shop_inventory.start()
    
    async def update_shop_status(self):
        channel = self.bot.get_channel(self.update_channel_id)
        if channel:
            embed = discord.Embed(title="商店商品庫存更新", color=discord.Color.green())
            embed.add_field(name="食物", value=f"{self.shop_data['food']['stock']} / {self.shop_data['food']['max_stock']}", inline=False)
            for key, potion in self.shop_data['potions'].items():
                embed.add_field(name=f"藥水 ({key.replace('_', '加成')})", value=f"{potion['stock']} / {potion['max_stock']}", inline=False)
            for key, equip in self.shop_data['equipment'].items():
                embed.add_field(name=f"{key.replace('_', '級裝備')}", value=f"{equip['stock']} / {equip['max_stock']}", inline=False)
            
            if self.shop_status_message_id:
                message = await channel.fetch_message(self.shop_status_message_id)
                await message.edit(embed=embed)
            else:
                message = await channel.send(embed=embed)
                self.shop_status_message_id = message.id
                
    
    @app_commands.command(name="角色遊戲_商店", description="角色遊戲專用商店") 
    async def shop(self, interaction: discord.Interaction):
        view = View()
        view.add_item(BuyButton(self, "food", "食物", "食物"))
        view.add_item(BuyButton(self, "potions", "攻擊力加成10% 藥水", "藥水 (攻擊力加成10%)", "attack_10"))
        view.add_item(BuyButton(self, "potions", "攻擊力加成30% 藥水", "藥水 (攻擊力加成30%)", "attack_30"))
        view.add_item(BuyButton(self, "equipment", "1級裝備", "1級裝備", "level_1"))
        view.add_item(BuyButton(self, "equipment", "2級裝備", "2級裝備", "level_2"))
        view.add_item(BuyButton(self, "equipment", "3級裝備", "3級裝備", "level_3"))
        await interaction.response.send_message("歡迎來到商店！請選擇你想購買的物品。\n 食物 1個100角色遊戲代幣 \n 10%加成藥水 1個150 \n 30%藥水加成 1000 \n 一級裝備一個300\n 二級裝備一個400\n三級裝備一個1000", view=view)
        
    @app_commands.command(name="角色遊戲_查庫存", description="查看商店商品庫存")
    async def check_stock(self, interaction: discord.Interaction):
        embed = discord.Embed(title="商店商品庫存", color=discord.Color.blue())
        embed.add_field(name="食物", value=f"{self.shop_data['food']['stock']} / {self.shop_data['food']['max_stock']}", inline=False)
        for key, potion in self.shop_data['potions'].items():
            embed.add_field(name=f"藥水 ({key.replace('_', '加成')})", value=f"{potion['stock']} / {potion['max_stock']}", inline=False)
        for key, equip in self.shop_data['equipment'].items():
            embed.add_field(name=f"{key.replace('_', '級裝備')}", value=f"{equip['stock']} / {equip['max_stock']}", inline=False)
        await interaction.response.send_message(embed=embed)
        
class BuyButton(Button):
    def __init__(self, cog, category, label, button_label, item_key=None):
        self.cog = cog
        self.category = category
        self.item_key = item_key
        item = cog.shop_data[category][item_key] if item_key else cog.shop_data[category]
        super().__init__(label=button_label, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        character_cog = self.cog.bot.get_cog('Character')
        character = character_cog.load_character(user_id)

        if not character:
            await interaction.response.send_message('你還沒有角色。請先創建一個角色。', ephemeral=True)
            return

        if character["banned"]:
            await interaction.response.send_message('你已被禁止使用RPG指令。', ephemeral=True)
            return

        item = self.cog.shop_data[self.category][self.item_key] if self.item_key else self.cog.shop_data[self.category]
        if item["stock"] <= 0:
            await interaction.response.send_message(f'{self.label} 已售罄。', ephemeral=True)
            return

        if character["tokens"] < item["price"]:
            await interaction.response.send_message(f'你的代幣不足以購買 {self.label}。', ephemeral=True)
            return

        character["tokens"] -= item["price"]
        item["stock"] -= 1

        if self.category == "food":
            character["inventory"].append({"type": "food", "name": "食物", "hp_increase": 20, "attack_boost": 1.1, "duration": 5})
        elif self.category == "potions":
            potion_name = "攻擊力加成10% 藥水" if self.item_key == "attack_10" else "攻擊力加成30% 藥水"
            attack_boost = 1.1 if self.item_key == "attack_10" else 1.3
            expiration_time = datetime.now() + timedelta(days=1)
            character["inventory"].append({"type": "potion", "name": potion_name, "attack_boost": attack_boost, "expiration": expiration_time.isoformat()})
        elif self.category == "equipment":
            level = int(self.item_key.split('_')[1])
            defense_boost = level * 0.05
            attack_boost = level * 0.05
            character["inventory"].append({"type": "equipment", "level": level, "defense_boost": defense_boost, "attack_boost": attack_boost})

        character_cog.save_character(user_id, character)
        self.cog.save_shop_data()
        await interaction.response.send_message(f'成功購買 {self.label}！', ephemeral=True)

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

class EquipButton(Button):
    def __init__(self, cog, item):
        self.cog = cog
        self.item = item
        super().__init__(label=f'穿上 {item["name"]}', style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        character_cog = self.cog.bot.get_cog('Character')
        character = character_cog.load_character(user_id)

        if self.item not in character["inventory"]:
            await interaction.response.send_message('你沒有這個物品。', ephemeral=True)
            return

        if self.item["type"] == "equipment":
            character["defense"] += self.item["defense_boost"]
            character["attack"] += self.item["attack_boost"]
            character["inventory"].remove(self.item)
            character_cog.save_character(user_id, character)
            await interaction.response.send_message(f'你穿上了 {self.item["name"]}。', ephemeral=True)
        else:
            await interaction.response.send_message('這個物品不能穿上。', ephemeral=True)

async def setup(bot):
    await bot.add_cog(rpg_Shop(bot))    