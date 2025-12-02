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
    """Generate Telegraph pages for catalog (called once at startup)"""
    global TELEGRAPH_LINKS
    import time
    
    logger.info("📝 Generating Telegraph pages...")
    
    try:
        # Group books by first letter
        books_by_letter = {}
        for book in BOOKS:
            first_letter = book['title'][0].upper()
            if not first_letter.isalpha():
                first_letter = '#'  # For numbers and special characters
            
            if first_letter not in books_by_letter:
                books_by_letter[first_letter] = []
            books_by_letter[first_letter].append(book)
        
        # Sort letters
        sorted_letters = sorted([l for l in books_by_letter.keys() if l != '#']) + (['#'] if '#' in books_by_letter else [])
        
        # Create Telegraph pages for each letter with delay to avoid flood control
        for i, letter in enumerate(sorted_letters):
            books = books_by_letter[letter]
            
            # Create HTML content for this letter
            html_content = f'<h3>📚 Moon Read Catalog - Letter {letter}</h3>'
            html_content += f'<p><strong>Books starting with "{letter}": {len(books)}</strong></p>'
            html_content += '<hr>'
            
            for idx, book in enumerate(books, 1):
                html_content += f'<p>{idx}. <a href="{book["link"]}">{book["title"]}</a></p>'
            
            # Create Telegraph page for this letter
            title = f'Moon Read Catalog - {letter}' if letter != '#' else 'Moon Read Catalog - Numbers & Special'
            
            try:
                response = telegraph.create_page(
                    title=title,
                    html_content=html_content,
                    author_name='Moon Read',
                    author_url='https://t.me/moon_read'
                )
                
                TELEGRAPH_LINKS[letter] = {
                    'url': f"https://telegra.ph/{response['path']}",
                    'count': len(books)
                }
                
                logger.info(f"✅ Created Telegraph page for letter {letter} ({len(books)} books)")
                
                # Add delay between requests to avoid flood control (10 seconds)
                if i < len(sorted_letters) - 1:  # Don't delay after last one
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"❌ Error creating page for {letter}: {e}")
                # Continue with other letters even if one fails
        
        logger.info(f"✅ Generated {len(TELEGRAPH_LINKS)} Telegraph pages successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating Telegraph pages: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = f"""
🌙 <b>Welcome to Moon Read Catalog Bot!</b> 📚

Find novels from our collection of <b>{len(BOOKS)}+ EPUBs</b>!

<b>How to use:</b>

🔍 <b>Search for a book:</b>
/search tempest
Example: /search villainess

📖 <b>Random book:</b>
/random

📋 <b>Browse by alphabet:</b>
/catalog - Browse A-Z with buttons!
Or type: KATALOG

📚 <b>Tutorial (Indonesian):</b>
/tutorial - Panduan lengkap

ℹ️ <b>Help:</b>
/help

Start searching now! 🚀
"""
    try:
        await update.message.reply_text(welcome_text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        await update.message.reply_text(f"Welcome to Moon Read! We have {len(BOOKS)}+ books. Use /help for commands.")


async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tutorial/guide for using Moon Read"""
    tutorial_text = """
📚 <b>Moon Read Tutorial - Panduan Lengkap</b>

<b>🌙 Tentang Moon Read:</b>
Moon Read adalah perpustakaan digital dengan 1000+ novel EPUB gratis!

<b>📱 Cara Menggunakan Bot:</b>

1️⃣ <b>Cari Buku:</b>
   Ketik: /search [kata kunci]
   Contoh: /search romance
   Contoh: /search villainess

2️⃣ <b>Lihat Katalog Lengkap:</b>
   Ketik: /catalog atau KATALOG
   Klik huruf untuk lihat semua buku

3️⃣ <b>Buku Random:</b>
   Ketik: /random
   Dapat rekomendasi acak!

<b>🔗 Link Penting:</b>
• Channel Utama: https://t.me/moon_read
• Bot Catalog: @MoonCatalogBot

<b>💡 Tips:</b>
✅ Gunakan kata kunci spesifik untuk hasil lebih baik
✅ Semua buku format EPUB (e-book)
✅ Download langsung dari Telegram

<b>❓ Butuh bantuan?</b>
Ketik /help untuk melihat semua perintah!
"""
    try:
        await update.message.reply_text(tutorial_text, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error sending tutorial: {e}")
        # Fallback without formatting
        await update.message.reply_text(
            "📚 Moon Read Tutorial\n\n"
            "Cara menggunakan:\n"
            "1. /search [keyword] - Cari buku\n"
            "2. /catalog - Lihat semua buku\n"
            "3. /random - Buku acak\n\n"
            "Channel: https://t.me/moon_read"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
📚 <b>Moon Read Catalog Bot - Help</b>

<b>Available Commands:</b>

🔍 <b>Search:</b>
• /search keyword - Search for books
• Example: /search romance
• Example: /search villainess tempest

📋 <b>Catalog:</b>
• /catalog or KATALOG - Browse with buttons!
• Click any letter to see Telegraph page
• All books organized alphabetically

📖 <b>Random:</b>
• /random - Get a random book recommendation

📊 <b>Statistics:</b>
• /stats - Show catalog statistics

📚 <b>Tutorial:</b>
• /tutorial - Complete guide (Indonesian)

<b>Search Tips:</b>
• Search is case-insensitive
• Use multiple keywords: /search fantasy romance
• Partial matches work (e.g., "temp" finds "Tempest")

<b>Need help?</b> Contact @moonreadteam
"""
    try:
        await update.message.reply_text(help_text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error sending help: {e}")
        await update.message.reply_text("Use /search, /catalog, /random, /stats, /tutorial")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for books using /search command"""
    import html
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a search keyword!\n\n"
            "<b>Example:</b>\n"
            "/search tempest\n"
            "/search villainess romance",
            parse_mode='HTML'
        )
        return
    
    keyword = ' '.join(context.args).lower()
    results = [book for book in BOOKS if keyword in book['title'].lower()]
    
    if not results:
        await update.message.reply_text(
            f"📭 No books found for: <b>{html.escape(keyword)}</b>\n\n"
            "Try different keywords!",
            parse_mode='HTML'
        )
        return
    
    limited_results = results[:20]
    
    message = f"🔍 <b>Search Results for: {html.escape(keyword)}</b>\n\n"
    message += f"Found <b>{len(results)}</b> book(s)\n"
    if len(results) > 20:
        message += f"<i>(Showing first 20 results)</i>\n"
    message += "\n"
    
    for i, book in enumerate(limited_results, 1):
        # Escape title to prevent entity parsing errors
        safe_title = html.escape(book['title'])
        message += f"{i}. <a href=\"{book['link']}\">{safe_title}</a>\n\n"
    
    if len(results) > 20:
        message += f"<i>...and {len(results) - 20} more results</i>\n"
        message += f"\n💡 Tip: Use more specific keywords to narrow results"
    
    try:
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error sending search results: {e}")
        # Fallback: Send without formatting
        simple_message = f"Found {len(results)} books for: {keyword}\n\n"
        for i, book in enumerate(limited_results, 1):
            simple_message += f"{i}. {book['title']}\n{book['link']}\n\n"
        await update.message.reply_text(simple_message, disable_web_page_preview=True)



async def random_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random book"""
    import html
    
    if not BOOKS:
        await update.message.reply_text("❌ Catalog not loaded. Please try again later.")
        return
    
    book = random.choice(BOOKS)
    safe_title = html.escape(book['title'])
    
    message = f"""
📖 <b>Random Book Recommendation</b>

<a href="{book['link']}">{safe_title}</a>

Want another? Type /random again!
"""
    try:
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error sending random book: {e}")
        await update.message.reply_text(f"📖 Random Book:\n\n{book['title']}\n{book['link']}", disable_web_page_preview=True)


async def catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show alphabet keyboard with Telegraph links"""
    
    # Check if Telegraph links are ready
    if not TELEGRAPH_LINKS:
        await update.message.reply_text(
            "⏳ Catalog is being prepared... Please try again in a moment.\n\n"
            "You can use /search keyword to find books in the meantime!"
        )
        return
    
    # Create inline keyboard with alphabet buttons (6 buttons per row)
    keyboard = []
    sorted_letters = sorted([l for l in TELEGRAPH_LINKS.keys() if l != '#']) + (['#'] if '#' in TELEGRAPH_LINKS else [])
    
    row = []
    for letter in sorted_letters:
        data = TELEGRAPH_LINKS[letter]
        button_text = f"{letter} ({data['count']})"
        # Use URL button to directly open Telegraph page
        row.append(InlineKeyboardButton(button_text, url=data['url']))
        
        if len(row) == 6 or letter == sorted_letters[-1]:  # 6 buttons per row
            keyboard.append(row)
            row = []
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
📚 <b>Moon Read Full Catalog</b>

Total Books: <b>{len(BOOKS)}</b>

🔤 <b>Click any letter to browse:</b>

Each button will open a Telegraph page with all books starting with that letter!
"""
    
    try:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error sending catalog: {e}")
        await update.message.reply_text(
            f"📚 Moon Read Catalog\n\nTotal Books: {len(BOOKS)}\n\nUse /search to find books!",
            reply_markup=reply_markup
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show catalog statistics"""
    
    if not BOOKS:
        await update.message.reply_text("❌ Catalog not loaded.")
        return
    
    # Count books by first letter
    letter_counts = {}
    for book in BOOKS:
        first_char = book['title'][0].upper()
        letter = first_char if first_char.isalpha() else '#'
        letter_counts[letter] = letter_counts.get(letter, 0) + 1
    
    message = f"📊 <b>Moon Read Catalog Statistics</b>\n\n"
    message += f"📚 <b>Total Books:</b> {len(BOOKS)}\n\n"
    message += f"🔤 <b>Books by Letter:</b>\n"
    
    # Show counts for each letter
    for letter in sorted(letter_counts.keys()):
        message += f"• {letter}: {letter_counts[letter]}\n"
    
    message += f"\n💡 Use /catalog to browse with buttons!"
    
    try:
        await update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error sending stats: {e}")
        simple_message = f"📊 Moon Read Statistics\n\nTotal Books: {len(BOOKS)}\n\nUse /catalog to browse!"
        await update.message.reply_text(simple_message)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages"""
    text = update.message.text
    
    # Handle KATALOG keyword
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
    
    # Generate Telegraph pages
    print("\n📝 Generating Telegraph catalog pages...")
    print("⏳ This will take about 4-5 minutes (10 sec delay between pages)")
    print("💡 The bot will accept commands after generation is complete\n")
    
    if not generate_telegraph_pages():
        print("⚠️  Warning: Failed to generate some Telegraph pages")
        print("Bot will still work, but /catalog might have issues")
    else:
        print(f"✅ Telegraph pages ready!")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tutorial", tutorial_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("random", random_book))
    application.add_handler(CommandHandler("catalog", catalog_command))
    application.add_handler(CommandHandler("katalog", catalog_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    print("\n" + "=" * 70)
    print("✅ Bot started successfully!")
    print("=" * 70)
    print("🔍 Search: /search keyword")
    print("📋 Catalog: /catalog or KATALOG (Telegraph + Buttons!)")
    print("📖 Random: /random")
    print("📊 Stats: /stats")
    print("📚 Tutorial: /tutorial (Indonesian)")
    print("=" * 70)
    print("\n🚀 Bot is running!\n")
    
    # Run bot (polling mode for Seenode)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
