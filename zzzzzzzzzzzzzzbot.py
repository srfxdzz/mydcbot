import asyncio
import time , os
from pyrogram import Client, filters

api_id = "14011503"
api_hash = "10f47cfbbcc7326db4365c54ca89e3df"
app = Client("userbot", api_id=api_id, api_hash=api_hash)

TARGET_CHAT_ID = -1002068015865

avatar_folder = "avtarbanner"

pics_folder = "pics"

async def save_media(message, is_avatar=False):
    """
    Save media files (either image or gif) to specific folders.
    :param message: The message object that may contain media.
    :param is_avatar: Boolean flag to save to the 'avatar' folder (for user profile pictures).
    :return: file_path where the media is saved.
    """
    try:
        if message.photo:
            print(message)
            file_path = os.path.join(avatar_folder if is_avatar else pics_folder, f"{message.id}.jpg")
            await message.download(file_path)
            return file_path
        elif message.document:
            if message.document.mime_type.startswith('image/'):
                file_path = os.path.join(pics_folder, f"{message.id}.jpg")
                await message.download(file_path)
                return file_path
            elif message.document.mime_type.startswith('video/'):
                file_path = os.path.join(pics_folder, f"{message.id}.mp4")
                await message.download(file_path)
                return file_path
        elif message.animation:
            # If it's a GIF (animation)
            file_path = os.path.join(pics_folder, f"{message.id}.gif")
            await message.download(file_path)
            return file_path
        else:
            return None
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None

async def send_message_and_wait(target_user_id):
    """
    Send a message to the target group and wait for a reply, removing the last 3 lines from the response.
    Save media (image, gif, etc.) in the appropriate folders.
    """
    try:
        # Ensure the app is started before sending messages
        if not app.is_connected:
            await app.start()  # This ensures the client is connected
        
        sent_message = await app.send_message(chat_id=TARGET_CHAT_ID, text=f"get {target_user_id}", disable_web_page_preview=True)
        
        # Wait for 5 seconds before checking for the reply
        await asyncio.sleep(5)

        async for message in app.get_chat_history(TARGET_CHAT_ID, limit=5):
            if message.reply_to_message_id == sent_message.id:
                # Check if the message has text and media
                if message.text:
                    lines = message.text.splitlines()
                    truncated_text = "\n".join(lines[:-3]) if len(lines) > 3 else ""
                    
                elif message.photo or message.document or message.animation:
                    # Save media (image or gif)
                    media_path = await save_media(message, is_avatar=False)  # Set `is_avatar=True` for user profile pics
                    if media_path:
                        return f"Media saved to {media_path}"
                    else:
                        return "No media found in the reply."
                else:
                    continue

        return "No text or media reply found."
    
    except Exception as e:
        return f"Error: {e}"

async def background_task():
    """
    This function will repeatedly send messages and wait for replies.
    You can change the logic to determine how often and what user IDs to send.
    """
    target_user_id = 12345678  # Example user ID, replace with your logic to select user IDs

    while True:
        response = await send_message_and_wait(target_user_id)
        print(f"Response: {response}")

        # Sleep or add a delay here before starting the next task
        await asyncio.sleep(10)  # Wait 10 seconds before sending the next message

# To run background tasks in an event loop
async def main():
    # Start the background task before app.run
    asyncio.create_task(background_task())

    # Start the Pyrogram client
    await app.start()

    # Keep the application running indefinitely
    while True:
        await asyncio.sleep(3600)  # Keep the bot running (1 hour)

if __name__ == "__main__":
    asyncio.run(main())
