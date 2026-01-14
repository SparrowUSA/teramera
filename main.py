import os
import asyncio
import time
from pyrogram import Client, filters
from terabox_utils import upload_to_terabox, get_share_link

# Railway Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
NDUS = os.getenv("TERABOX_NDUS")
DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL"))

app = Client("tb_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
upload_queue = asyncio.Queue()

async def worker():
    while True:
        msg, video_index = await upload_queue.get()
        local_file = None
        status = await app.send_message(DUMP_CHANNEL, f"Processing Video {video_index}...")
        
        try:
            # 1. Download
            await status.edit(f"📥 Downloading Video {video_index}...")
            local_file = await msg.download()
            
            # 2. Upload
            await status.edit(f"📤 Uploading Video {video_index} to TeraBox...")
            fs_id = upload_to_terabox(local_file, NDUS)
            
            if fs_id:
                # 3. Share
                link = get_share_link(NDUS, fs_id)
                await status.edit(f"✅ **Video {video_index} Done!**\n🔗 {link}")
            else:
                await status.edit(f"❌ TeraBox rejected upload for Video {video_index}. Check logs.")
                
        except Exception as e:
            await status.edit(f"⚠️ Error: {str(e)}")
        finally:
            if local_file and os.path.exists(local_file):
                os.remove(local_file)
            upload_queue.task_done()
            await asyncio.sleep(2)

@app.on_message(filters.command("bulk", prefixes=".") & filters.me)
async def bulk_upload(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.edit("Usage: `.bulk [Start_Link] [End_Link]`")

    start_id = int(args[1].split('/')[-1])
    end_id = int(args[2].split('/')[-1])
    
    await message.edit("🔍 Scanning...")
    
    count = 0
    for m_id in range(start_id, end_id + 1):
        try:
            m = await client.get_messages(message.chat.id, m_id)
            if m.video or m.document:
                count += 1
                await upload_queue.put((m, count))
        except: continue
        
    await message.edit(f"✅ Queued {count} videos.")

async def main():
    async with app:
        # FIX: Resolve the Peer ID at startup
        try:
            await app.get_chat(DUMP_CHANNEL)
            print("Successfully linked to Dump Channel!")
        except Exception as e:
            print(f"Peer Resolution Error: {e}")
            
        asyncio.create_task(worker())
        await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
