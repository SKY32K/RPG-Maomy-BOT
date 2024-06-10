import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import json
import os

class BuyButton(Button):
    def __init__(self, cog, item_name, price, description):
        self.cog = cog
        self.item_name = item_name
        self.price = price
        self.description = description
        super().__init__(label=f'购买 {item_name}', style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await self.cog.buy_item(interaction, self.item_name)

class RPGGroup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guilds_dir = './date/rpg/guilds'
        self.users_file = './date/rpg/users.json'
        if not os.path.exists(self.guilds_dir):
            os.makedirs(self.guilds_dir)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)

    def load_user(self, user_id):
        character_file = f'./date/characters/{user_id}.json'
        if os.path.exists(character_file):
            with open(character_file, 'r') as f:
                return json.load(f)
        return None

    def load_guild(self, guild_name):
        guild_file = os.path.join(self.guilds_dir, f'{guild_name}.json')
        if os.path.exists(guild_file):
            with open(guild_file, 'r') as f:
                return json.load(f)
        return None

    def save_guild(self, guild_name, data):
        guild_file = os.path.join(self.guilds_dir, f'{guild_name}.json')
        with open(guild_file, 'w') as f:
            json.dump(data, f, indent=4)

    def load_user_guild(self, user_id):
        with open(self.users_file, 'r') as f:
            users_data = json.load(f)
        return users_data.get(str(user_id), {}).get("guild")

    def save_user_guild(self, user_id, guild_name):
        with open(self.users_file, 'r') as f:
            users_data = json.load(f)
        user_id = str(user_id)
        if user_id not in users_data:
            users_data[user_id] = {}
        users_data[user_id]["guild"] = guild_name
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=4)

    def delete_user_guild(self, user_id):
        with open(self.users_file, 'r') as f:
            users_data = json.load(f)
        user_id = str(user_id)
        if user_id in users_data and "guild" in users_data[user_id]:
            del users_data[user_id]["guild"]
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=4)

    @app_commands.command(name="角色遊戲_公會資訊", description="查看公會的詳細資訊")
    async def guild_info(self, interaction: discord.Interaction):
        guild_name = self.load_user_guild(interaction.user.id)
        if not guild_name:
            await interaction.response.send_message('你不在任何公會中。', ephemeral=True)
            return

        guild_data = self.load_guild(guild_name)
        if not guild_data:
            await interaction.response.send_message('找不到公會資訊。', ephemeral=True)
            return

        leader = self.bot.get_user(guild_data["leader"])
        member_names = [self.bot.get_user(member_id).name for member_id in guild_data["members"]]

        embed = discord.Embed(title=f"公會: {guild_data['name']}", color=discord.Color.blue())
        embed.add_field(name="領導者", value=leader.name if leader else "未知", inline=False)
        embed.add_field(name="等級", value=str(guild_data["level"]), inline=False)
        embed.add_field(name="經驗", value=str(guild_data["experience"]), inline=False)
        embed.add_field(name="代幣", value=str(guild_data["tokens"]), inline=False)
        embed.add_field(name="成員", value="\n".join(member_names), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="角色遊戲_公會商品", description="公会商店专用")
    async def guild_shop(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = self.load_user(user_id)

        if not user_data:
            await interaction.response.send_message('你还没有创建角色。')
            return

        # 定义商品
        shop_items = {
            "装备1": {"price": 100, "description": "1级装备"},
            "装备2": {"price": 500, "description": "2级装备"},
            "装备3": {"price": 3000, "description": "3级装备"},
            "药水1": {"price": 500, "description": "加成10%"},
            "药水2": {"price": 1500, "description": "加成30%"},
            "称号": {"price": 10000, "description": "可自由更改，限制3次"},
            "公会改名卡": {"price": 10000, "description": "需公会等级达2"}
        }

        # 创建按钮视图
        view = View()
        for item_name, item_info in shop_items.items():
            view.add_item(BuyButton(self, item_name, item_info["price"], item_info["description"]))

        await interaction.response.send_message('欢迎来到公会商店！以下是本店的商品列表：', view=view)

    async def buy_item(self, interaction: discord.Interaction, item_name: str):
        user_id = str(interaction.user.id)
        user_data = self.load_user(user_id)

        if not user_data:
            await interaction.response.send_message('你还没有创建角色。')
            return

        shop_items = {
            "装备1": {"price": 100, "description": "1级装备"},
            "装备2": {"price": 500, "description": "2级装备"},
            "装备3": {"price": 3000, "description": "3级装备"},
            "药水1": {"price": 500, "description": "加成10%"},
            "药水2": {"price": 1500, "description": "加成30%"},
            "称号": {"price": 10000, "description": "可自由更改，限制3次"},
            "公会改名卡": {"price": 10000, "description": "需公会等级达2"}
        }

        if item_name not in shop_items:
            await interaction.response.send_message('该商品不存在。')
            return

        item_info = shop_items[item_name]
        price = item_info["price"]

        if user_data["tokens"] < price:
            await interaction.response.send_message('你的代币不足以购买该商品。')
            return

        # 更新用户库存
        if "inventory" not in user_data:
            user_data["inventory"] = []

        user_data["inventory"].append({
            "name": item_name,
            "price": price,
            "description": item_info["description"]
        })

        # 扣除代币
        user_data["tokens"] -= price

        # 写入更新后的角色文件
        character_file = f'characters/{user_id}.json'
        with open(character_file, 'w') as f:
            json.dump(user_data, f)

        await interaction.response.send_message(f'成功购买 {item_name}！')

    @app_commands.command(name="角色遊戲_創建公會", description="需要1000及10等")
    @app_commands.describe(name="公会名称")
    async def create_guild(self, interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        character = self.load_user(user_id)
    
        if not character:
            await interaction.response.send_message('你还没有角色。')
            return
    
        if character["level"] < 10:
            await interaction.response.send_message('等级不足10，无法创建公会。')
            return
    
        if character["tokens"] < 1000:
            await interaction.response.send_message('代币不足1000，无法创建公会。')
            return
    
        if self.load_user_guild(user_id):
            await interaction.response.send_message('你已经加入了一个公会，无法创建新的公会。')
            return
    
        guild_name = name
        guild_data = {
            "name": guild_name,
            "leader": interaction.user.id,
            "members": [interaction.user.id],
            "level": 1,
            "experience": 0,
            "tokens": 0
        }
        self.save_guild(guild_name, guild_data)
        self.save_user_guild(user_id, guild_name)
    
        # Deduct tokens from the user
        character["tokens"] -= 1000
    
        # Save the updated user data
        character_file = f'characters/{user_id}.json'
        with open(character_file, 'w') as f:
            json.dump(character, f)
    
        await interaction.response.send_message(f'公会 {guild_name} 创建成功！')
        
    @app_commands.command(name="角色遊戲_刪除公會", description="删除公会-公会会长")
    async def delete_guild(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_name = self.load_user_guild(user_id)

        if not guild_name:
            await interaction.response.send_message('你没有加入任何公会。')
            return

        guild_data = self.load_guild(guild_name)

        if not guild_data:
            await interaction.response.send_message('公会不存在或已被删除。')
            return

        if interaction.user.id != guild_data["leader"]:
            await interaction.response.send_message('你不是公会会长，无法删除公会。')
            return

        # 删除公会文件
        os.remove(os.path.join(self.guilds_dir, f'{guild_name}.json'))
        # 删除所有成员的公会信息
        for member_id in guild_data["members"]:
            self.delete_user_guild(member_id)
        
        await interaction.response.send_message('公会删除成功！')

    @app_commands.command(name="角色遊戲_转让公会", description="转让公会-公会会长")
    async def transfer_guild(self, interaction: discord.Interaction, new_leader: discord.Member):
        user_id = str(interaction.user.id)
        guild_name = self.load_user_guild(user_id)

        if not guild_name:
            await interaction.response.send_message('你没有加入任何公会。')
            return

        guild_data = self.load_guild(guild_name)

        if not guild_data:
            await interaction.response.send_message('公会不存在或已被删除。')
            return

        if interaction.user.id != guild_data["leader"]:
            await interaction.response.send_message('你不是公会会长，无法转让公会。')
            return

        guild_data["leader"] = new_leader.id
        self.save_guild(guild_name, guild_data)
        self.save_user_guild(new_leader.id, guild_name)
        await interaction.response.send_message(f'公会已成功转让给 {new_leader.display_name}！')

    @app_commands.command(name="角色遊戲_邀请人加入", description="邀请人加入公会")
    async def invite_to_guild(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(interaction.user.id)
        guild_name = self.load_user_guild(user_id)

        if not character:
                await interaction.response.send_message('你还没有角色。')
                return
        

        if not guild_name:
            await interaction.response.send_message('你没有加入任何公会。')
            return

        guild_data = self.load_guild(guild_name)

        if not guild_data:
            await interaction.response.send_message('公会不存在或已被删除。')
            return

        if interaction.user.id != guild_data["leader"]:
            await interaction.response.send_message('你不是公会会长，无法邀请人加入公会。')
            return

        if member.id in guild_data["members"]:
            await interaction.response.send_message(f'{member.display_name} 已经是公会成员。')
            return

        guild_data["members"].append(member.id)
        self.save_guild(guild_name, guild_data)
        self.save_user_guild(member.id, guild_name)
        await interaction.response.send_message(f'{member.display_name} 已成功加入公会！')

    @app_commands.command(name="角色遊戲_审批加入公会", description="审批加入公会")
    async def approve_join_request(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(interaction.user.id)
        guild_name = self.load_user_guild(user_id)

        if not guild_name:
            await interaction.response.send_message('你没有加入任何公会。')
            return

        guild_data = self.load_guild(guild_name)

        if not guild_data:
            await interaction.response.send_message('公会不存在或已被删除。')
            return

        if interaction.user.id != guild_data["leader"]:
            await interaction.response.send_message('你不是公会会长，无法审批加入公会。')
            return

        if member.id in guild_data["members"]:
            await interaction.response.send_message(f'{member.display_name} 已经是公会成员。')
            return

        guild_data["members"].append(member.id)
        self.save_guild(guild_name, guild_data)
        self.save_user_guild(member.id, guild_name)
        await interaction.response.send_message(f'{member.display_name} 的加入申请已批准！')

    @app_commands.command(name="角色遊戲_公会升级", description="公会升级要使用的指令")
    async def guild_upgrade(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_name = self.load_user_guild(user_id)

        if not guild_name:
            await interaction.response.send_message('你没有加入任何公会。')
            return

        guild_data = self.load_guild(guild_name)

        if not guild_data:
            await interaction.response.send_message('公会不存在或已被删除。')
            return

        exp_needed = 100 * guild_data["level"]
        if guild_data["experience"] >= exp_needed:
            guild_data["level"] += 1
            guild_data["experience"] -= exp_needed
            self.save_guild(guild_name, guild_data)
            await interaction.response.send_message(f'公会已成功升级到等级 {guild_data["level"]}！')
        else:
            await interaction.response.send_message('公会经验值不足，无法升级。')

async def setup(bot):
    await bot.add_cog(RPGGroup(bot))    