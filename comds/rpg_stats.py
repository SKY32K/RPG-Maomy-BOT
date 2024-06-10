import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
import json
import os
import asyncio

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.characters_dir = './date/characters'

    def load_character(self, user_id):
        character_file = os.path.join(self.characters_dir, f'{user_id}.json')
        if os.path.exists(character_file):
            with open(character_file, 'r') as f:
                return json.load(f)
        return None

    def save_character(self, user_id, character):
        if not os.path.exists(self.characters_dir):
            os.makedirs(self.characters_dir)
        character_file = os.path.join(self.characters_dir, f'{user_id}.json')
        with open(character_file, 'w') as f:
            json.dump(character, f, indent=4)

class QuestCompletionHandler:
    def __init__(self, bot, quests):
        self.bot = bot
        self.quests = quests

    async def complete_quest(self, interaction, character, user_id, quest_type, quest_name):
        quest = self.quests[quest_type][quest_name]
        character_cog = self.bot.get_cog('CharacterCog')

        # 特殊條件檢查
        if quest_type == "final":
            if quest_name == "最終-2" and character["level"] < 20:
                await interaction.response.send_message("你需要達到20級才能完成此任務。")
                return
            elif quest_name == "最終-3" and not character.get("guild"):
                await interaction.response.send_message("你需要加入/創建一個公會才能完成此任務。")
                return
            elif quest_name == "最終-4" and character.get("guild_level", 0) < 3:
                await interaction.response.send_message("你的公會需要達到3級才能完成此任務。")
                return
            elif quest_name == "最終-5":
                hp, atk, defn = character["hp"], character["atk"], character["def"]
                if not ((hp > 100 and atk > 150 and defn > 100) or character.get("potion_count", 0) > 0):
                    await interaction.response.send_message("你的狀態不符合打敗艾爾文巫師的條件。")
                    return

        # 獎勵分發邏輯
        character["tokens"] += quest["rewards"].get("tokens", 0)
        # 可以添加更多獎勵處理邏輯
        character.setdefault("completed_quests", []).append(quest_name)

        # 任务完成后的处理逻辑
        completed_quests = character["completed_quests"]
        if len(completed_quests) == 10:
            await interaction.user.send("艾爾文巫師正在攻擊城堡，請求援助！")
        if len(completed_quests) == 15:
            await interaction.response.send_message("你已經完成了15個任務，'最後一章節'已經解鎖！")

        del character['active_quest']
        character_cog.save_character(user_id, character)
        await interaction.response.send_message(f'恭喜你完成了{quest_type}任務: {quest_name}！你獲得了以下獎勵:\n{quest["rewards"]}')

class QuestSelectionModal(ui.Modal, title="選擇任務"):
    quest_type = ui.TextInput(label="任務類型", placeholder="main, side, final")
    quest_name = ui.TextInput(label="任務名稱", placeholder="輸入任務名稱")

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        quest_type = self.quest_type.value
        quest_name = self.quest_name.value
        user_id = str(interaction.user.id)
        character_cog = self.bot.get_cog('CharacterCog')
        character = character_cog.load_character(user_id)

        if not character:
            await interaction.response.send_message('你還沒有角色。請先創建一個角色。', ephemeral=True)
            return

        if quest_type not in self.bot.quests:
            await interaction.response.send_message("請指定有效的任務類型：main, side 或 final", ephemeral=True)
            return

        if quest_name not in self.bot.quests[quest_type]:
            await interaction.response.send_message(f'沒有名為 {quest_name} 的{quest_type}任務。', ephemeral=True)
            return

        quest = self.bot.quests[quest_type][quest_name]
        if 'active_quest' in character:
            await interaction.response.send_message('你已經有一個進行中的任務。請先完成或取消它。', ephemeral=True)
            return

        completed_quests = character.get('completed_quests', [])
        if quest_type == "final":
            if len(completed_quests) < 15:
                await interaction.response.send_message('你需要完成至少15個任務才能解鎖最終章節。', ephemeral=True)
                return
            if len(completed_quests) < 10:
                await interaction.response.send_message('最終章節正在編輯中。', ephemeral=True)
                return

        character['active_quest'] = {"type": quest_type, "name": quest_name}
        character_cog.save_character(user_id, character)
        
        await interaction.response.send_message(f'你開始了任務: {quest_name}\n{quest["description"]}', ephemeral=True)

        if quest_type == "final" and quest_name == "最終-1":
            await asyncio.sleep(quest["duration"])
            await interaction.followup.send(f'你已經耗時 {quest["duration"]/60} 分鐘找到巫師國的位置。任務完成。')
            quest_completion_handler = QuestCompletionHandler(self.bot, self.bot.quests)
            await quest_completion_handler.complete_quest(interaction, character, user_id, quest_type, quest_name)
            
class QuestSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quests_file = './data/rpg/quests.json'
        self.load_quests()

    def load_quests(self):
        if os.path.exists(self.quests_file):
            with open(self.quests_file, 'r') as f:
                self.quests = json.load(f)
        else:
            self.quests = {"main": {}, "side": {}, "final": {}}

    def save_quests(self):
        with open(self.quests_file, 'w') as f:
            json.dump(self.quests, f, indent=4)

    @app_commands.command(name="角色遊戲_查看可用的任務", description="查看可用的任務")
    async def quests(self, interaction: discord.Interaction, quest_type: str):
        if quest_type not in ["main", "side", "final"]:
            await interaction.response.send_message("請指定任務類型：main, side 或 final")
            return

        available_quests = '\n'.join(self.quests[quest_type].keys())
        await interaction.response.send_message(f'可用的{quest_type}任務:\n{available_quests}')

    @app_commands.command(name="角色遊戲_查看任務詳情", description="查看任務詳情")
    async def quest(self, interaction: discord.Interaction, quest_type: str, quest_name: str):
        if quest_type not in ["main", "side", "final"]:
            await interaction.response.send_message("請指定任務類型：main, side 或 final")
            return

        if quest_name in self.quests[quest_type]:
            quest = self.quests[quest_type][quest_name]
            await interaction.response.send_message(f'任務名稱: {quest_name}\n描述: {quest["description"]}\n挑戰: {quest["challenges"]}\n獎勵: {quest["rewards"]}')
        else:
            await interaction.response.send_message(f'沒有名為 {quest_name} 的{quest_type}任務。')

    @app_commands.command(name="角色遊戲_完成一個任務", description="完成一個任務")
    async def completequest(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        character_cog = self.bot.get_cog('CharacterCog')
        character = character_cog.load_character(user_id)

        if not character:
            await interaction.response.send_message('你還沒有角色。請先創建一個角色。')
            return

        if 'active_quest' not in character:
            await interaction.response.send_message('你沒有進行中的任務。')
            return

        quest_type = character['active_quest']['type']
        quest_name = character['active_quest']['name']
        quest_completion_handler = QuestCompletionHandler(self.bot, self.quests)
        await quest_completion_handler.complete_quest(interaction, character, user_id, quest_type, quest_name)

    @app_commands.command(name="列出可用任務", description="列出所有可用的任務")
    async def list_quests(self, interaction: discord.Interaction):
        quest_list = ""
        for quest_type, quests in self.quests.items():
            quest_list += f"{quest_type.capitalize()}:\n"
            for quest_name in quests:
                quest_list += f"  - {quest_name}\n"
        
        if quest_list:
            await interaction.response.send_message(f"所有可用的任務:\n{quest_list}")
        else:
            await interaction.response.send_message("目前沒有可用的任務。")

    @app_commands.command(name="開始一個任務", description="開始一個新的任務")
    async def startquest(self, interaction: discord.Interaction):
        await interaction.response.send_modal(QuestSelectionModal(self.bot))

async def setup(bot):
    await bot.add_cog(CharacterCog(bot))
    await bot.add_cog(QuestSystem(bot))