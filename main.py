from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
import re
from collections import defaultdict
from datetime import datetime

TOKEN = 'xxxxxxxxxx:xxxxxxxxxxxxxxxxx'#修改为自己bot的token


async def fetch_gallery_metadata(gallery_id: str, gallery_token: str, domain: str):
    if domain == "e-hentai.org":
        api_url = "https://api.e-hentai.org/api.php"
    elif domain == "exhentai.org":
        api_url = "https://api.exhentai.org/api.php"
    else:
        return None

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
    match = re.search(r'https://(e-hentai\.org|exhentai\.org)/g/(\d+)/([0-9a-f]+)/?', url)
    if not match:
        await update.message.reply_text("URL格式不正确，请确保使用正确的URL。")
        return

    domain, gallery_id, gallery_token = match.groups()
    metadata = await fetch_gallery_metadata(gallery_id, gallery_token, domain)

    if not metadata:
        await update.message.reply_text("未找到画廊信息。")
        return

    # 在上传者前加#
    uploader = f"#{metadata['uploader']}" if metadata.get('uploader') else "未知"
    # 在上传日期之前添加正常时间格式
    upload_date = datetime.utcfromtimestamp(metadata['posted']).strftime('%Y-%m-%d %H:%M:%S')

# Process and format tags
    tags_by_category = defaultdict(list)
    for tag in metadata['tags']:
        category, detail = tag.split(':', 1)  # Split each tag into category and detail
        tags_by_category[category].append(detail)
    
    # Build the formatted tag string
    formatted_tags = []
    for category, details in tags_by_category.items():
        # 在为每个细节前加#之前，替换空格为下划线
        details_str = ' '.join([f"#{detail.replace(' ', '_')}" for detail in details])

        formatted_tags.append(f"{category}:{details_str}")
    
    formatted_tags_str = '\n'.join(formatted_tags)  # Join all formatted tags with newline

    # 使用上传日期而不是时间戳
    message_text = (
    f"名称: {metadata['title']}\n"
    f"上传者: {uploader}\n"
    f"上传日期: {upload_date}\n"  # 使用正常时间格式
    f"评分: {metadata['rating']}\n"
    f"标签:\n{formatted_tags_str}\n"
    f"画廊URL: {url}\n"

)

    await update.message.reply_photo(photo=metadata['thumb'], caption=message_text)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("gallery", gallery_command))
    application.run_polling()

if __name__ == '__main__':
    main()
