import discord
from discord.ext import commands, tasks
import random
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
fasting_channel_id = os.getenv('FASTING_CHANNEL_ID')


intents = discord.Intents.all()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

class LoseWeight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = None
        self.total_time_min = 0
        self.fasting_channel_id = int(fasting_channel_id) if fasting_channel_id and fasting_channel_id.isdigit() else None
        self.fasting_channel = self.bot.get_channel(self.fasting_channel_id)
        self.is_fasting_record_mode = False
        self.is_fasting_countdown_mode = False

    @tasks.loop(minutes=1)
    async def check_time_method(self):
        print("check_time_method is called")
        now = datetime.now()
        delta = now - self.start_time
        days, seconds = delta.days, delta.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        await self.fasting_channel.send(f"已經斷食  {days}天{hours}小時{minutes}分鐘")

    @tasks.loop(hours=1)
    async def check_time(self):
        if self.is_fasting:
            if self.start_time and self.fasting_channel:
                now = datetime.now()
                if now.hour == 10 or now.hour == 15:
                    if random.randint(1, 20) == 1:  # 5% 
                        await self.fasting_channel.send(f"這餐可以吃飯(5%)")
                if now.minute == 0:
                    await self.check_time_method()


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.name == "mu0420":
            print(f"Received message: {message.content} from: {message.channel}")

        if message.channel.name == "斷食":
            if message.content.startswith('start') and self.is_fasting_countdown_mode == False:
                parts = message.content.split()
                if len(parts) == 1:
                    print("[info] 紀錄模式")
                    if message.content == "start" :
                        self.start_time = datetime.now()
                        self.is_fasting_record_mode = True
                        await message.channel.send("開始斷食紀錄")
                else:
                    self.is_fasting_countdown_mode = True
                    parts.pop(0)
                    temp = 0
                    for x in parts:
                        if x[-1] == 'd':
                            temp = x[:-1]
                            self.total_time_min += (int(temp)*24*60)
                            await self.fasting_channel.send(f'剩餘時間{self.total_time_min}')
                        elif x[-1] == 'h':
                            temp = x[:-1]
                            self.total_time_min += (int(temp)*60)
                            await self.fasting_channel.send(f'剩餘時間{self.total_time_min}')
                        elif x[-1] == 'm':
                            temp = x[:-1]
                            self.total_time_min += (int(temp))
                            await self.fasting_channel.send(f'剩餘時間{self.total_time_min}')
                    
                    print(self.total_time_min)

            if message.content == "time":
                if self.is_fasting_countdown_mode:
                    print("讀到'時間'")
                    await self.fasting_channel.send(f'剩餘時間{self.total_time_min}')
                else:
                    print("讀到'時間'")
                    await self.check_time_method()

            elif message.content == "end":
                if self.is_fasting_countdown_mode:
                    print("讀到'時間'")

                    # 將總分鐘轉換為天、小時和分鐘
                    total_minutes = self.total_time_min
                    days, remainder = divmod(total_minutes, 1440)  # 一天有1440分鐘
                    hours, minutes = divmod(remainder, 60)

                    # 格式化字符串
                    time_str = f"已經斷食  {days}天{hours}小時{minutes}分鐘"

                    # 發送到頻道
                    await self.fasting_channel.send(time_str)
                else:
                    await message.channel.send("斷食結束")
                    await self.check_time_method()
                    self.start_time = None
                    self.is_fasting_record_mode = False

        await self.bot.process_commands(message)



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.add_cog(LoseWeight(bot))




bot.run(discord_token)
