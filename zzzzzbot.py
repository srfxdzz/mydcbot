from pyrogram import Client, filters
import time



api_id = "14011503"
api_hash = "10f47cfbbcc7326db4365c54ca89e3df"

app = Client("userbot", api_id=api_id, api_hash=api_hash)


# TARGET_CHAT_ID = -1002068015865  

# TARGET_USER_ID = 776702343       

# async def send_message_and_wait(TARGET_USER_ID):
#     try:
#         async with app:
#             sent_message = await app.send_message(chat_id=TARGET_CHAT_ID, text=f"get {TARGET_USER_ID}")

#             time.sleep(3)
#             async for message in app.get_chat_history(TARGET_CHAT_ID, limit=5):

#                 if message.reply_to_message_id == sent_message.id :
#                     return message.text , True
                    
#     except Exception as e:
#         return e , False

                    



# # Run the async function
# app.run(send_message_and_wait())






TARGET_CHAT_ID = -1002068015865  #

async def send_message_and_wait(target_user_id):

    """
    Send a message to the target group and wait for a reply, removing last 3 lines from the response.
    """

    try:

        sent_message = await app.send_message(chat_id=TARGET_CHAT_ID, text=f"get {target_user_id}", disable_web_page_preview=True)
        
        time.sleep(3) 


        async for message in app.get_chat_history(TARGET_CHAT_ID, limit=5):
            if message.reply_to_message_id == sent_message.id:
        
                if message.text:
                 
                    lines = message.text.splitlines()
                    truncated_text = "\n".join(lines[:-3]) if len(lines) > 3 else ""  

                    
                    
                    return truncated_text
                else:
                    
                    continue

        text="No text reply found."
        return  text

    except Exception as e:
        # Send error back to the command issuer
        text=f"Error: {e}"
        return text
    
    



