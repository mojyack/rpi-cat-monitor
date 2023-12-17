import os
import sys
import threading
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import discord

client = None
channel = None
ready = False

def init():
    global client
    global channel

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    # discord.utils.get(channels.guild.channels, name="")

    @client.event
    async def on_ready():
        global ready

        ready = True
        print(f"We have logged in as {client.user}")
    
    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
    
        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

def start(token):
    threading.Thread(target=client.run, args=(token,)).start()

def send_message(channel_id, text, files=[]):
    channel = client.get_channel(channel_id)
    if channel == None:
        print("no such channel")
        return
    client.loop.create_task(channel.send(text, files=[discord.File(p) for p in files]))

def stop():
    client.loop.create_task(client.close())
