import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
from discord.ui import Button, View




def run_bot():
    load_dotenv()
    TOKEN = "MTMwNzAxMjIwODAyNjE4OTg3Ng.GUDvm9.tW1Jf1ld9_h0rngZTl7ALcmhH0zKc5Y7KS-XHE"
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    queues = {}
    voice_clients = {}
    yt_dl_options = {"format": "bestaudio/best", "noplaylist": True}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -filter:a "volume=0.50"'
    }

    @client.event
    async def on_ready():
        print(f'{client.user} is now jamming')

    @client.event
    async def on_message(message):
        if message.content.startswith("play"):
            try:
                # Join the voice channel
                voice_client = await message.author.voice.channel.connect()
                voice_clients[voice_client.guild.id] = voice_client
            except Exception as e:
                print(e)

            try:
                # Get the song name or URL from the message
                query = " ".join(message.content.split()[1:])
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))

                # Extract the URL of the first result
                spng__url = data['entries'][0]
                song_title = spng__url.get("title", "Unknown Title")
                song_url_ = data['entries'][0]['url']
                print(song_title)
                await play_song(message, song_url_)

                # Create and send a message with play/pause/stop buttons
                controls = MusicControls(message.guild.id)  # Pass the guild ID to track the music state
                await message.channel.send(f"Now playing: {song_title}", view=controls)

            except Exception as e:
                print(e)

        if message.content.startswith("pause"):
            try:
                voice_clients[message.guild.id].pause()
            except Exception as e:
                print(e)

        if message.content.startswith("resume"):
            try:
                voice_clients[message.guild.id].resume()
            except Exception as e:
                print(e)

        if message.content.startswith("stop"):
            try:
                voice_clients[message.guild.id].stop()
                await voice_clients[message.guild.id].disconnect()
            except Exception as e:
                print(e)

        if message.content.startswith("volume"):
            try:
                volume = int(message.content.split()[1])  # Assuming volume is between 10 and 100
                if 10 <= volume <= 100:
                    normalized_volume = volume / 100  # Convert to a value between 0 and 1
                    ffmpeg_options['options'] = f'-vn -filter:a "volume={normalized_volume}"'
                    await message.channel.send(f"Volume set to {volume}%")
                else:
                    await message.channel.send("Invalid volume. Please provide a value between 10 and 100.")
            except ValueError:
                await message.channel.send("Invalid volume. Please provide a numeric value between 10 and 100.")


    async def play_song(message, song_url):
        titmleee = song_url
        voice_client = voice_clients[message.guild.id]
        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdl.extract_info(song_url, download=False))
        song_url = data['url']
        player = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)

        voice_client.play(player)

    @client.event
    async def on_voice_state_update(member, before, after):
        if before.channel is not None and len(before.channel.members) == 1:  # Last person leaves the voice channel
            if member != client.user:
                voice_clients[before.channel.guild.id].stop()
                await voice_clients[before.channel.guild.id].disconnect()

    class MusicControls(View):
        def __init__(self, guild_id):
            super().__init__()
            self.timeout = 60
            self.guild_id = guild_id
            self.voice_client = voice_clients.get(self.guild_id)

        def update_buttons(self):
            """ Updates buttons based on the current state of the music """
            if self.voice_client is None:
                return

            # Update buttons based on the music state
            if self.voice_client.is_playing():
                self.children[0].label = "Pause"
                self.children[0].style = discord.ButtonStyle.red
                self.children[1].label = "Stop"
                self.children[1].style = discord.ButtonStyle.danger
            elif self.voice_client.is_paused():
                self.children[0].label = "Resume"
                self.children[0].style = discord.ButtonStyle.green
                self.children[1].label = "Stop"
                self.children[1].style = discord.ButtonStyle.danger
            else:
                self.children[0].label = "Play"
                self.children[0].style = discord.ButtonStyle.green
                self.children[1].label = "Stop"
                self.children[1].style = discord.ButtonStyle.danger








        def update__buttons(self):
            """ Updates buttons based on the current state of the music """
            if self.voice_client is None:
                self.children[1].label = "Stopped"
                self.children[1].style = discord.ButtonStyle.danger

            
            else:
                self.children[1].label = "Stopped"
                self.children[1].style = discord.ButtonStyle.danger

        @discord.ui.button(label="Play", style=discord.ButtonStyle.green)
        async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.voice_client.is_paused():
                self.voice_client.resume()
                await interaction.response.edit_message(content="Resuming music!")
            else:
                await interaction.response.edit_message(content="Music is already playing.")
            self.update_buttons()  # Update buttons after action

        @discord.ui.button(label="Pause", style=discord.ButtonStyle.red)
        async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.voice_client.pause()
            await interaction.response.edit_message(content="Music paused.")
            self.update_buttons()  # Update buttons after action




        @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
        async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.voice_client.stop()
            await self.voice_client.disconnect()
            await interaction.response.edit_message(content="Stopped and disconnected.", view=self.create_stopped_view())

        def create_stopped_view(self):
            stopped_view = discord.ui.View()
            stopped_view.add_item(discord.ui.Button(label="Music is stopped", style=discord.ButtonStyle.danger, disabled=True))
            return stopped_view



        @discord.ui.button(label="Volume", style=discord.ButtonStyle.primary)
        async def volume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message("Please type `volume <value>` to adjust the volume between 0 and 1.")
        
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            """Checks if the interaction is from the same guild"""
            if interaction.guild.id != self.guild_id:
                await interaction.response.send_message("This is not your server.", ephemeral=True)
                return False
            return True

    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()
