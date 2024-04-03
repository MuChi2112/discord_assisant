import discord
from discord.ext import commands, tasks
from flask import Flask, request, jsonify
import threading
import random
from datetime import datetime
import os
from dotenv import load_dotenv

# Flask app initialization
app = Flask(__name__)

# Flask route for checking the bot's status
@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'The bot is running!'})

# Function to run the Flask app in a separate thread
def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Load environment variables
load_dotenv()

discord_token = os.getenv('DISCORD_TOKEN')
fasting_channel_id = os.getenv('FASTING_CHANNEL_ID')

# Discord bot initialization
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

class LoseWeight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = None
        self.total_time_min = 0
        self.fasting_channel_id = int(fasting_channel_id) if fasting_channel_id and fasting_channel_id.isdigit() else None
        self.fasting_channel = None
        self.is_fasting_record_mode = False
        self.is_fasting_countdown_mode = False

        self.check_time_method.start()

    def cog_unload(self):
        self.check_time_method.cancel()

    @tasks.loop(minutes=1)
    async def check_time_method(self):
        if self.start_time and self.fasting_channel:
            now = datetime.now()
            delta = now - self.start_time
            days, seconds = delta.days, delta.seconds
            hours = days * 24 + seconds // 3600
            minutes = (seconds % 3600) // 60
            await self.fasting_channel.send(f"已經斷食  {days}天{hours}小時{minutes}分鐘")

    @commands.Cog.listener()
    async def on_ready(self):
        if self.fasting_channel_id:
            self.fasting_channel = self.bot.get_channel(self.fasting_channel_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.id != self.fasting_channel_id:
            return

        content = message.content.lower()

        if content.startswith('start'):
            self.start_time = datetime.now()
            self.is_fasting_record_mode = True
            await message.channel.send("開始斷食紀錄。")

        elif content == 'end':
            if self.is_fasting_record_mode:
                await message.channel.send("斷食結束。")
                self.is_fasting_record_mode = False

        elif content == 'time':
            await self.check_time_method()

# Register the cog with the bot
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.add_cog(LoseWeight(bot))

# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()

# Start the Discord bot
bot.run(discord_token)
