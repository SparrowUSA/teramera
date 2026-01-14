import os
import asyncio
from pyrogram import Client, filters
from terabox_utils import upload_via_browser

# CONFIG
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
        status = await app.send_message(DUMP_CHANNEL, f"🛠 **Starting Task {video_index}**")

        try:
            # Download from TG
            await status.edit(f"📥 Downloading Video {video_index}...")
            local_file = await msg.download()
            
            # Upload via Browser
            await status.edit(f"🌐 [Browser] Uploading Video {video_index}...")
            share_url = await upload_via_browser(local_file, NDUS)
            
            if share_url:
                await status.edit(f"✅ **Video {video_index} Uploaded!**\n📂 Check your TeraBox Root folder.")
            else:
                await status.edit(f"❌ Browser Upload Failed for Video {video_index}.")

        except Exception as e:
            await status.edit(f"⚠️ Error: {str(e)}")
        finally:
            if local_file and os.path.exists(local_file):
                os.remove(local_file)
            upload_queue.task_done()

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
        m = await client.get_messages(message.chat.id, m_id)
        if m and (m.video or m.document):
            count += 1
            await upload_queue.put((m, count))
            
    await message.edit(f"✅ Queued {count} items.")

async def main():
    async with app:
        # Peer resolution
        try:
            await app.get_chat(DUMP_CHANNEL)
            print("Bot is online and Linked!")
        except:
            print("Warning: Could not resolve Dump Channel ID.")
            
        asyncio.create_task(worker())
        await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
