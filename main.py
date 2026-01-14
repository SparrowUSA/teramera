import os
import asyncio
from pyrogram import Client, filters
from terabox_utils import upload_to_terabox, get_share_link

# Config from Railway Environment Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
NDUS = os.getenv("TERABOX_NDUS")
DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL"))

app = Client("tb_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
upload_queue = asyncio.Queue()

async def worker():
    """Background worker to process videos one by one"""
    while True:
        msg, video_index, total = await upload_queue.get()
        local_file = None
        try:
            # Notify progress
            print(f"Processing {video_index}/{total}")
            
            # 1. Download from TG
            local_file = await msg.download()
            
            # 2. Upload to TeraBox
            fs_id = upload_to_terabox(local_file, NDUS)
            
            if fs_id:
                # 3. Get Share Link
                share_url = get_share_link(NDUS, fs_id)
                
                # 4. Post to Channel
                text = f"✅ **Video {video_index}**\n🔗 [TeraBox Link]({share_url})"
                await app.send_message(DUMP_CHANNEL, text)
            else:
                await app.send_message(DUMP_CHANNEL, f"❌ Failed to upload Video {video_index}")

        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            if local_file and os.path.exists(local_file):
                os.remove(local_file)
            upload_queue.task_done()
            # Wait 5 seconds to avoid spamming/hitting rate limits
            await asyncio.sleep(5)

@app.on_message(filters.command("bulk", prefixes=".") & filters.me)
async def bulk_cmd(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.edit("Usage: `.bulk [Start_Link] [End_Link]`")

    # Extract IDs from links
    try:
        start_id = int(args[1].split('/')[-1])
        end_id = int(args[2].split('/')[-1])
    except:
        return await message.edit("Invalid links provided.")

    await message.edit("🔍 Scanning for videos...")
    
    count = 0
    # Collect messages in range
    messages = await client.get_messages(message.chat.id, list(range(start_id, end_id + 1)))
    
    for m in messages:
        if m and (m.video or m.document):
            count += 1
            await upload_queue.put((m, count, "Pending")) # Added placeholder total logic

    await message.edit(f"📦 Added {count} videos to the queue.")

async def main():
    async with app:
        print("Bot Started!")
        asyncio.create_task(worker())
        await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
