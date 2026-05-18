#!/usr/bin/env python3
"""
Moon Read Catalog Bot - Seenode Deployment
Bot: @MoonCatalogBot
With Telegraph integration and inline keyboard
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import csv
import logging
import os
import random
import time
from telegraph import Telegraph

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

# Initialize Telegraph
telegraph = Telegraph()
telegraph.create_account(short_name='MoonRead', author_name='Moon Read Catalog')

# Load catalog data
BOOKS = []
TELEGRAPH_LINKS = {}  # Cache for Telegraph links

MAX_BOOKS_PER_PAGE = 300  # Safe limit per Telegraph page


def load_catalog():
    """Load books from CSV file"""
    global BOOKS
    try:
        with open('titles_and_links_alphabetical.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            BOOKS = list(reader)
        logger.info(f"✅ Loaded {len(BOOKS)} books from catalog")
        return True
    except Exception as e:
        logger.error(f"❌ Error loading catalog: {e}")
        BOOKS = []
        return False


def generate_telegraph_pages():
    """Generate Telegraph pages for catalog, splitting large letters into sub-pages"""
    global TELEGRAPH_LINKS

    logger.info("📝 Generating Telegraph pages...")

    try:
        # Group books by first letter
        books_by_letter = {}
        for book in BOOKS:
            first_letter = book['title'][0].upper()
            if not first_letter.isalpha():
                first_letter = '#'
            if first_letter not in books_by_letter:
                books_by_letter[first_letter] = []
            books_by_letter[first_letter].append(book)

        sorted_letters = sorted([l for l in books_by_letter.keys() if l != '#']) + (['#'] if '#' in books_by_letter else [])

        page_count = 0

        for letter in sorted_letters:
            books = books_by_letter[letter]

            # Split into chunks if too many books
            chunks = [books[i:i+MAX_BOOKS_PER_PAGE] for i in range(0, len(books), MAX_BOOKS_PER_PAGE)]
            total_chunks = len(chunks)

            letter_pages = []

            for chunk_idx, chunk in enumerate(chunks):
                if total_chunks > 1:
                    page_label = f"{letter} ({chunk_idx+1}/{total_chunks})"
                    title = f'Moon Read Catalog - {letter} Part {chunk_idx+1}'
                else:
                    page_label = letter
                    if letter == '#':
                        title = 'Moon Read Catalog - Numbers & Special'
                    else:
                        title = f'Moon Read Catalog - {letter}'

                start_num = chunk_idx * MAX_BOOKS_PER_PAGE + 1

                html_content = f'<h3>📚 Moon Read Catalog - Letter {letter}</h3>'
                if total_chunks > 1:
                    html_content += f'<p><strong>Part {chunk_idx+1} of {total_chunks} | Books {start_num}–{start_num+len(chunk)-1}</strong></p>'
                html_content += f'<p><strong>Total "{letter}": {len(books)} books</strong></p>'
                html_content += '<hr>'

                for idx, book in enumerate(chunk, start_num):
                    html_content += f'<p>{idx}. <a href="{book["link"]}">{book["title"]}</a></p>'

                try:
                    response = telegraph.create_page(
                        title=title,
                        html_content=html_content,
                        author_name='Moon Read',
                        author_url='https://t.me/moon_read'
                    )

                    url = f"https://telegra.ph/{response['path']}"
                    letter_pages.append({
                        'url': url,
                        'label': page_label,
                        'count': len(chunk)
                    })

                    logger.info(f"✅ Created page: {title} ({len(chunk)} books)")
                    page_count += 1

                    # Delay to avoid Telegraph flood control
                    time.sleep(10)

                except Exception as e:
                    logger.error(f"❌ Error creating page for {letter} part {chunk_idx+1}: {e}")
                    # Continue with remaining chunks/letters

            if letter_pages:
                TELEGRAPH_LINKS[letter] = {
                    'pages': letter_pages,
                    'count': len(books),
                    'multi': total_chunks > 1
                }

        logger.info(f"✅ Generated {page_count} Telegraph pages for {len(TELEGRAPH_LINKS)} letters!")
        return True

    except Exception as e:
        logger.error(f"❌ Error generating Telegraph pages: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = f"""
🌙 *Welcome to Moon Read Catalog Bot!* 📚

Find novels from our collection of *{len(BOOKS)}+ EPUBs*\\!

*How to use:*

🔍 *Search for a book:*
`/search tempest`
Example: `/search villainess`

📖 *Random book:*
`/random`

📋 *Browse by alphabet:*
`/catalog` \\- Browse A\\-Z with buttons\\!
Or type: `KATALOG`

ℹ️ *Help:*
`/help`

Start searching now\\! 🚀
"""
    await update.message.reply_text(welcome_text, parse_mode='MarkdownV2')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
📚 *Moon Read Catalog Bot \\- Help*

*Available Commands:*

🔍 *Search:*
• `/search keyword` \\- Search for books
• Example: `/search romance`
• Example: `/search villainess tempest`

📋 *Catalog:*
• `/catalog` or `KATALOG` \\- Browse with buttons\\!
• Click any letter to see Telegraph page
• All books organized alphabetically

📖 *Random:*
• `/random` \\- Get a random book recommendation

📊 *Statistics:*
• `/stats` \\- Show catalog statistics

*Search Tips:*
• Search is case\\-insensitive
• Use multiple keywords: `/search fantasy romance`
• Partial matches work \\(e\\.g\\. "temp" finds "Tempest"\\)

*Need help?* Contact @moonreadteam
"""
    await update.message.reply_text(help_text, parse_mode='MarkdownV2')


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for books using /search command"""

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a search keyword!\n\n"
            "Example:\n"
            "/search tempest\n"
            "/search villainess romance"
        )
        return

    keyword = ' '.join(context.args).lower()
    results = [book for book in BOOKS if keyword in book['title'].lower()]

    if not results:
        await update.message.reply_text(
            f"📭 No books found for: {keyword}\n\n"
            "Try different keywords!"
        )
        return

    limited_results = results[:20]

    message = f"🔍 Search Results for: {keyword}\n\n"
    message += f"Found {len(results)} book(s)\n"
    if len(results) > 20:
        message += "(Showing first 20 results)\n"
    message += "\n"

    for i, book in enumerate(limited_results, 1):
        message += f"{i}. [{book['title']}]({book['link']})\n\n"

    if len(results) > 20:
        message += f"...and {len(results) - 20} more results\n"
        message += "\n💡 Tip: Use more specific keywords to narrow results"

    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def random_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random book"""
    if not BOOKS:
        await update.message.reply_text("❌ Catalog not loaded. Please try again later.")
        return

    book = random.choice(BOOKS)

    message = (
        f"📖 Random Book Recommendation\n\n"
        f"[{book['title']}]({book['link']})\n\n"
        f"Want another? Type /random again!"
    )
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show alphabet keyboard with Telegraph links"""

    if not TELEGRAPH_LINKS:
        await update.message.reply_text(
            "⏳ Catalog sedang dipersiapkan...\n\n"
            "Gunakan /search keyword untuk cari buku dulu!"
        )
        return

    keyboard = []
    sorted_letters = sorted([l for l in TELEGRAPH_LINKS.keys() if l != '#']) + (['#'] if '#' in TELEGRAPH_LINKS else [])

    row = []
    for letter in sorted_letters:
        data = TELEGRAPH_LINKS[letter]

        if data['multi']:
            # Multiple sub-pages for this letter
            for page_info in data['pages']:
                row.append(InlineKeyboardButton(
                    f"{page_info['label']} ({page_info['count']})",
                    url=page_info['url']
                ))
                if len(row) == 6:
                    keyboard.append(row)
                    row = []
        else:
            # Single page for this letter
            row.append(InlineKeyboardButton(
                f"{letter} ({data['count']})",
                url=data['pages'][0]['url']
            ))
            if len(row) == 6:
                keyboard.append(row)
                row = []

    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"📚 Moon Read Full Catalog\n\n"
        f"Total Books: {len(BOOKS)}\n\n"
        f"🔤 Klik huruf untuk browse:\n\n"
        f"Setiap tombol akan membuka halaman Telegraph dengan semua buku berawalan huruf tersebut!"
    )

    await update.message.reply_text(message, reply_markup=reply_markup)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show catalog statistics"""

    if not BOOKS:
        await update.message.reply_text("❌ Catalog not loaded.")
        return

    letter_counts = {}
    for book in BOOKS:
        first_char = book['title'][0].upper()
        letter = first_char if first_char.isalpha() else '#'
        letter_counts[letter] = letter_counts.get(letter, 0) + 1

    message = f"📊 Moon Read Catalog Statistics\n\n"
    message += f"📚 Total Books: {len(BOOKS)}\n\n"
    message += f"🔤 Books by Letter:\n"

    for letter in sorted(letter_counts.keys()):
        message += f"• {letter}: {letter_counts[letter]}\n"

    message += f"\n💡 Use /catalog to browse with buttons!"

    await update.message.reply_text(message)


async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tutorial link"""
    await update.message.reply_text(
        "📚 Moon Read Tutorial\n\n"
        "🔗 https://t.me/Moonread_Tutor",
        disable_web_page_preview=False
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages"""
    text = update.message.text

    if text.lower() == 'katalog':
        await catalog_command(update, context)


def main():
    """Start the bot"""
    print("=" * 70)
    print("🤖 MOON READ CATALOG BOT - @MoonCatalogBot")
    print("🌐 Deployed on Seenode.com")
    print("=" * 70)

    # Load catalog
    print("📚 Loading catalog...")
    if not load_catalog():
        print("❌ Failed to load catalog!")
        return

    print(f"✅ Loaded {len(BOOKS)} books")

    # Estimate time
    books_by_letter = {}
    for book in BOOKS:
        fl = book['title'][0].upper()
        if not fl.isalpha():
            fl = '#'
        books_by_letter[fl] = books_by_letter.get(fl, 0) + 1

    total_pages = sum(
        (count + MAX_BOOKS_PER_PAGE - 1) // MAX_BOOKS_PER_PAGE
        for count in books_by_letter.values()
    )
    est_minutes = (total_pages * 10) // 60

    print(f"\n📝 Generating Telegraph catalog pages...")
    print(f"⏳ Estimated ~{total_pages} pages, ~{est_minutes} minutes")
    print(f"💡 Bot akan aktif setelah semua halaman selesai dibuat\n")

    if not generate_telegraph_pages():
        print("⚠️  Warning: Failed to generate some Telegraph pages")
        print("Bot will still work, but /catalog might be incomplete")
    else:
        print(f"✅ Telegraph pages ready!")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("random", random_book))
    application.add_handler(CommandHandler("catalog", catalog_command))
    application.add_handler(CommandHandler("katalog", catalog_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("tutorial", tutorial_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("\n" + "=" * 70)
    print("✅ Bot started successfully!")
    print("=" * 70)
    print("🔍 Search: /search keyword")
    print("📋 Catalog: /catalog or KATALOG")
    print("📖 Random: /random")
    print("📊 Stats: /stats")
    print("=" * 70)
    print("\n🚀 Bot is running!\n")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
