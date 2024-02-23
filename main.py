from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
import re

TOKEN = '7072529241:AAE0d8ZkzDAe_wa2FWeCN8dKAd11S4vS91g'

async def fetch_gallery_metadata(gallery_id: str, gallery_token: str):
    api_url = "https://api.e-hentai.org/api.php"
    request_body = {
        "method": "gdata",
        "gidlist": [[int(gallery_id), gallery_token]],
        "namespace": 1
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json=request_body)
        response_data = response.json()
        return response_data['gmetadata'][0] if response_data['gmetadata'] else None

async def gallery_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("请提供画廊URL。格式：/gallery [URL]")
        return

    url = ' '.join(context.args)
    match = re.search(r'https://e-hentai\.org/g/(\d+)/([0-9a-f]+)/?', url)
    if not match:
        await update.message.reply_text("URL格式不正确，请确保使用正确的e-hentai画廊URL。")
        return

    gallery_id, gallery_token = match.groups()
    metadata = await fetch_gallery_metadata(gallery_id, gallery_token)

    if not metadata:
        await update.message.reply_text("未找到画廊信息。")
        return

    message_text = (
        f"名称: {metadata['title']}\n"
        f"上传者: {metadata['uploader']}\n"
        f"上传日期: {metadata['posted']}\n"
        f"标签: {', '.join(metadata['tags'])}\n"
        f"画廊URL: https://e-hentai.org/g/{gallery_id}/{gallery_token}/\n"
    )

    await update.message.reply_photo(photo=metadata['thumb'], caption=message_text)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("gallery", gallery_command))
    application.run_polling()

if __name__ == '__main__':
    main()
  
