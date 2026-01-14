import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from terabox_utils import upload_to_terabox, get_share_link

# --- CONFIGURATION ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
NDUS = os.getenv("TERABOX_NDUS")
DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL"))

app = Client("tb_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
upload_queue = asyncio.Queue()

# --- HELPER FUNCTIONS ---
def progress_bar(current, total):
    """Generates a visual progress bar string"""
    percentage = current * 100 / total
    completed = int(percentage / 10)
    return f"[{'■' * completed}{'□' * (10 - completed)}] {percentage:.1f}%"

async def worker():
    """Background worker to process uploads one by one"""
    while True:
        msg, video_index, total_queued = await upload_queue.get()
        local_file = None
        status_msg = await app.send_message(DUMP_CHANNEL, f"⏳ Starting Video {video_index}...")

        try:
            # 1. Download with progress
            last_edit = 0
            async def progress(current, total):
                nonlocal last_edit
                if time.time() - last_edit > 5:  # Edit every 5 seconds to avoid flood
                    await status_msg.edit(f"📥 **Downloading {video_index}/{total_queued}**\n{progress_bar(current, total)}")
                    last_edit = time.time()

            local_file = await msg.download(progress=progress)
            
            # 2. Upload to TeraBox
            await status_msg.edit(f"📤 **Uploading {video_index} to TeraBox...**")
            fs_id = upload_to_terabox(local_file, NDUS)
            
            if fs_id:
                # 3. Generate Share Link
                share_url = get_share_link(NDUS, fs_id)
                await status_msg.edit(
                    f"✅ **Video {video_index} Completed**\n\n"
                    f"🔗 [TeraBox Link]({share_url})",
                    disable_web_page_preview=False
                )
            else:
                await status_msg.edit(f"❌ TeraBox Upload Failed for Video {video_index}")

        except Exception as e:
            print(f"Error: {e}")
            await status_msg.edit(f"❌ Error on Video {video_index}: {str(e)}")
        
        finally:
            # Clean up local storage for Railway
            if local_file and os.path.exists(local_file):
                os.remove(local_file)
            upload_queue.task_done()
            await asyncio.sleep(3) # Small gap between tasks

# --- COMMAND HANDLERS ---
@app.on_message(filters.command("bulk", prefixes=".") & filters.me)
async def bulk_cmd(client, message):
    args = message.text.split()
    if len(args) < 3:
        return await message.edit("Usage: `.bulk [Start_Link] [End_Link]`")

    try:
        start_id = int(args[1].split('/')[-1])
        end_id = int(args[2].split('/')[-1])
        chat_id = message.chat.id
    except:
        return await message.edit("❌ **Invalid links.** Ensure they are from this chat.")

    await message.edit(f"🔍 **Scanning messages {start_id} to {end_id}...**")
    
    count = 0
    # Process range
    for msg_id in range(start_id, end_id + 1):
        try:
            m = await client.get_messages(chat_id, msg_id)
            # Filter for videos or video-documents
            if m and (m.video or (m.document and "video" in m.document.mime_type)):
                count += 1
                await upload_queue.put((m, count, "Unknown")) # Total is calculated after scan
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            continue
    
    await message.edit(f"📦 **Queued {count} videos.** Check the dump channel for progress!")

# --- STARTUP ---
async def main():
    async with app:
        print("UserBot is running...")
        # Start the background worker
        worker_task = asyncio.create_task(worker())
        # Keep the script alive
        await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
