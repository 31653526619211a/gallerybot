import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
import re
from collections import defaultdict
from datetime import datetime

# 加载环境变量
load_dotenv()

# 读取环境变量
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def fetch_gallery_metadata(gallery_id: str, gallery_token: str, domain: str):
    api_url = "https://api.e-hentai.org/api.php"
    request_body = {
        "method": "gdata",
        "gidlist": [[int(gallery_id), gallery_token]],
        "namespace": 1
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=request_body)
            response.raise_for_status()  # 这将对4XX或5XX响应抛出异常
            response_data = response.json()
            return response_data.get('gmetadata', [None])[0]
    except Exception as e:
        print(f"请求过程中出现问题: {e}")
        return None

async def fetch_first_image_url(gallery_page_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(gallery_page_url)
        if response.status_code == 200:
            match = re.search(r'<a href="(https://exhentai\.org/s/[a-zA-Z0-9]+/\d+-1)">', response.text)
            if match:
                return match.group(1)
    return None

async def gallery_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("请提供画廊URL。格式：/gallery [URL]")
        return

    url = ' '.join(context.args)
    match = re.search(r'https://(e-hentai\.org|exhentai\.org)/g/(\d+)/([0-9a-f]+)/?', url)
    if not match:
        await update.message.reply_text("URL格式不正确，请确保使用正确的URL。")
        return

    domain, gallery_id, gallery_token = match.groups()
    metadata = await fetch_gallery_metadata(gallery_id, gallery_token, domain)
    if not metadata:
        await update.message.reply_text("未找到画廊信息。")
        return

    gallery_page_url = f"https://{domain}/g/{gallery_id}/{gallery_token}/"
    first_image_url = await fetch_first_image_url(gallery_page_url)
    if not first_image_url:
        first_image_url = metadata['thumb']  # 若未找到第一张图片，使用元数据中的缩略图

    # 格式化消息文本
    uploader = metadata.get('uploader', "未知")
    upload_date = datetime.utcfromtimestamp(int(metadata['posted'])).strftime('%Y-%m-%d %H:%M:%S')
    tags_by_category = defaultdict(list)
    for tag in metadata['tags']:
        category, detail = tag.split(':', 1)
        tags_by_category[category].append(detail.replace(' ', '_'))

    formatted_tags = [f"    {category}: {' '.join([f'#{detail}' for detail in details])}" for category, details in tags_by_category.items()]
    formatted_tags_str = '\n'.join(formatted_tags)

    message_text = (
        f"名称: {metadata['title']}\n"
        f"上传者: {uploader}\n"
        f"上传日期: {upload_date}\n"
        f"评分: {metadata['rating']}\n"
        f"标签:\n{formatted_tags_str}\n"
        f"表站链接: https://e-hentai.org/g/{gallery_id}/{gallery_token}/\n"
        f"里站链接: https://exhentai.org/g/{gallery_id}/{gallery_token}/\n"
    )

    await update.message.reply_photo(photo=first_image_url, caption=message_text)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("gallery", gallery_command))
    application.run_polling()

if __name__ == '__main__':
    main()
