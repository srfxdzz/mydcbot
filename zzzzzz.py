import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from discord.ui import Button, View

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Global variables
voice_clients = {}
song_queue = {}  # Queue for each guild
ytdl = yt_dlp.YoutubeDL({"format": "bestaudio/best", "noplaylist": True})
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.75"'
}

# Bot Events
@client.event
async def on_ready():
    print(f'{client.user} is now online and ready to jam!')

@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Commands
    if message.content.startswith("play"):
        await handle_play(message)

    elif message.content.startswith("pause"):
        await handle_pause(message)

    elif message.content.startswith("resume"):
        await handle_resume(message)

    elif message.content.startswith("stop"):
        await handle_stop(message)

    elif message.content.startswith("volume"):
        await handle_volume(message)

    elif message.content.startswith("queue"):
        await handle_queue(message)

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel and len(before.channel.members) == 1 and member != client.user:
        voice_client = voice_clients.pop(before.channel.guild.id, None)
        if voice_client:
            await voice_client.disconnect()

# Music Command Handlers
async def handle_play(message):
    try:
        # Join voice channel if not already connected
        voice_client = voice_clients.get(message.guild.id)
        if not voice_client or not voice_client.is_connected():
            voice_client = await message.author.voice.channel.connect()
            voice_clients[message.guild.id] = voice_client

        # Get song details
        query = " ".join(message.content.split()[1:])
        data = await asyncio.get_event_loop().run_in_executor(
            None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False)
        )
        song_info = data['entries'][0]
        song_url = song_info['url']
        song_title = song_info.get("title", "Unknown Title")
        controls = MusicControls(message.guild.id)

        # Add to queue
        if message.guild.id not in song_queue:
            song_queue[message.guild.id] = []
        
        song_queue[message.guild.id].append({
            'url': song_url,
            'title': song_title
        })

        # If no song is currently playing, start playing the first song
        if not voice_client.is_playing():
            await play_next_song(voice_client, message.guild.id)
        
        await message.channel.send(f"Added to queue: **{song_title}**")

    except Exception as e:
        print(f"Error in play command: {e}")
        await message.channel.send("Failed to play the song. Make sure you're in a voice channel and provide a valid query.")

async def handle_pause(message):
    voice_client = voice_clients.get(message.guild.id)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await message.channel.send("Music paused.")
    else:
        await message.channel.send("No music is playing.")

async def handle_resume(message):
    voice_client = voice_clients.get(message.guild.id)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await message.channel.send("Music resumed.")
    else:
        await message.channel.send("No music is paused.")

async def handle_stop(message):
    voice_client = voice_clients.pop(message.guild.id, None)
    if voice_client:
        voice_client.stop()
        await voice_client.disconnect()
        song_queue[message.guild.id] = []  # Clear queue
        await message.channel.send("Music stopped and bot disconnected.")
    else:
        await message.channel.send("No music is playing.")

async def handle_volume(message):
    try:
        volume = int(message.content.split()[1])
        if 10 <= volume <= 100:
            normalized_volume = volume / 100
            ffmpeg_options['options'] = f'-vn -filter:a "volume={normalized_volume}"'
            await message.channel.send(f"Volume set to {volume}%.")
        else:
            await message.channel.send("Volume must be between 10 and 100.")
    except (ValueError, IndexError):
        await message.channel.send("Please specify a volume between 10 and 100.")

async def play_song(voice_client, song_url):
    try:
        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(song_url, download=False))
        song_url = data['url']
        player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)
        voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, voice_client.guild.id), client.loop))
    except Exception as e:
        print(f"Error in playing song: {e}")

async def play_next_song(voice_client, guild_id):
    """Play the next song in the queue."""
    controls = MusicControls(guild_id)
    if guild_id in song_queue and song_queue[guild_id]:
        song = song_queue[guild_id].pop(0)  # Get the first song in the queue
        await play_song(voice_client, song['url'])
        
        await voice_client.channel.send(f"Now playing: **{song['title']}**", view=controls)
    else:
        await voice_client.channel.send("Queue is empty. Bot disconnected.")

async def handle_queue(message):
    """Display the current song queue."""
    guild_id = message.guild.id
    if guild_id in song_queue and song_queue[guild_id]:
        queue_list = "\n".join([f"{index+1}. {song['title']}" for index, song in enumerate(song_queue[guild_id])])
        await message.channel.send(f"Current Queue:\n{queue_list}")
    else:
        await message.channel.send("The queue is empty.")

# Music Control Buttons
class MusicControls(View):
    def __init__(self, guild_id):
        super().__init__()
        self.timeout = 60
        self.guild_id = guild_id
        self.voice_client = voice_clients.get(self.guild_id)
        self.current_volume = 50  # Default volume is 50%

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.red)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = voice_clients.get(self.guild_id)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.edit_message(content="Music paused.")
        else:
            await interaction.response.edit_message(content="No music is playing.")

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.green)
    async def resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = voice_clients.get(self.guild_id)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.edit_message(content="Music resumed.")
        else:
            await interaction.response.edit_message(content="No music is paused.")

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.voice_client.stop()
        await self.voice_client.disconnect()
        await interaction.response.edit_message(content="Stopped and disconnected.", view=self.create_stopped_view())

    def create_stopped_view(self):
        stopped_view = discord.ui.View()
        stopped_view.add_item(discord.ui.Button(label="Music is stopped", style=discord.ButtonStyle.danger, disabled=True))
        return stopped_view

    @discord.ui.button(label="Volume Up", style=discord.ButtonStyle.primary)
    async def volume_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_volume < 100:
            self.current_volume += 10
            if self.current_volume > 100:
                self.current_volume = 100
            normalized_volume = self.current_volume / 100
            ffmpeg_options['options'] = f'-vn -filter:a "volume={normalized_volume}"'
            await interaction.response.edit_message(content=f"Volume set to {self.current_volume}%")
        else:
            await interaction.response.edit_message(content="Volume is already at maximum (100%).")

    @discord.ui.button(label="Volume Down", style=discord.ButtonStyle.primary)
    async def volume_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_volume > 10:
            self.current_volume -= 10
            if self.current_volume < 10:
                self.current_volume = 10
            normalized_volume = self.current_volume / 100
            ffmpeg_options['options'] = f'-vn -filter:a "volume={normalized_volume}"'
            await interaction.response.edit_message(content=f"Volume set to {self.current_volume}%")
        else:
            await interaction.response.edit_message(content="Volume is already at minimum (10%).")

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip the current song and play the next one."""
        voice_client = voice_clients.get(self.guild_id)
        if voice_client:
            voice_client.stop()  # Stop the current song
            await interaction.response.edit_message(content="Song skipped.")
            await play_next_song(voice_client, self.guild_id)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks if the interaction is from the same guild"""
        if interaction.guild.id != self.guild_id:
            await interaction.response.send_message("This is not your server.")
            return False
        return True

# Run the bot
if __name__ == "__main__":
    client.run(TOKEN)
