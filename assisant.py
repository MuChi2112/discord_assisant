import discord
from discord.ext import commands, tasks
from flask import Flask, request, jsonify
import threading
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from threading import Thread

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)
# Flask app initialization
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()


load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
fasting_channel_id = os.getenv('FASTING_CHANNEL_ID')





class LoseWeight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.fasting_channel_id = int(fasting_channel_id) if fasting_channel_id and fasting_channel_id.isdigit() else None
        self.fasting_channel = self.bot.get_channel(self.fasting_channel_id)
        self.is_fasting_record_mode = False
        self.is_fasting_countdown_mode = False
        self.fasting_end_time = None
        self.start_time = None
        self.total_time_min = 0

    @tasks.loop(minutes=1)
    async def check_time_method(self):
        print("check_time_method is called")
        now = datetime.now()
        delta = now - self.start_time
        days, seconds = delta.days, delta.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        await self.fasting_channel.send(f"已經斷食  {days}天{hours}小時{minutes}分鐘")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.name == "mu0420":
            print(f"Received message: {message.content} from: {message.channel}")

        if message.channel.name == "斷食":
            if message.content.startswith('start') and self.is_fasting_countdown_mode == False and self.is_fasting_record_mode == False:
                self.total_time_min = 0
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
                        elif x[-1] == 'h':
                            temp = x[:-1]
                            self.total_time_min += (int(temp)*60)
                        elif x[-1] == 'm':
                            temp = x[:-1]
                            self.total_time_min += (int(temp))
                    
                    print(self.total_time_min)

                    now = datetime.now()
                    self.fasting_end_time = None
                    self.fasting_end_time = now + timedelta(minutes=self.total_time_min)

                    # 使用 strftime 方法來正確格式化日期和時間
                    formatted_end_time = self.fasting_end_time.strftime('%m/%d %H:%M')

                    # 確保格式化的字符串被正確地用於消息發送
                    await self.fasting_channel.send(f'斷食結束日期為: {formatted_end_time}')

            if message.content == "time":
                if self.is_fasting_countdown_mode:
                    print("讀到'時間'")
                    now = datetime.now()
                    # 獲取從現在到斷食結束的時間間隔
                    fasting_time_remaining = self.fasting_end_time - now

                    # 將 timedelta 對象分解為天、小時和分鐘
                    days = fasting_time_remaining.days
                    hours, remainder = divmod(fasting_time_remaining.seconds, 3600)
                    minutes = (remainder // 60)

                    # 格式化字符串
                    if days > 0:
                        time_str = f"距離斷食結束還有 {days}天{hours}小時{minutes}分鐘"
                    else:
                        time_str = f"距離斷食結束還有 {hours}小時{minutes}分鐘"

                    # 發送到頻道
                    await self.fasting_channel.send(time_str)

                else:
                    print("讀到'時間'")
                    await self.check_time_method()

            elif message.content == "end":
                if self.is_fasting_countdown_mode:
                    now = datetime.now()
                    fasting_time_remaining = self.fasting_end_time - now

                    # 將 timedelta 對象分解為天、小時和分鐘
                    days = fasting_time_remaining.days
                    hours, remainder = divmod(fasting_time_remaining.seconds, 3600)
                    minutes = (remainder // 60)

                    # 格式化字符串
                    if days > 0:
                        time_str = f"距離斷食結束還有 {days}天{hours}小時{minutes}分鐘"
                    else:
                        time_str = f"距離斷食結束還有 {hours}小時{minutes}分鐘"

                    # 發送到頻道
                    await self.fasting_channel.send(time_str)
                    self.is_fasting_countdown_mode = False
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

# Start the Flask app in a separate thread
if __name__ == "__main__":
    load_dotenv()  # 加载环境变量
    discord_token = os.getenv('DISCORD_TOKEN')  # 获取Discord Token

    keep_alive()  # 启动 Flask web服务器
    bot.run(discord_token)  # 使用Discord Token启动bot
