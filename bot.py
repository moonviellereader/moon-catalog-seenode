#!/usr/bin/env python3
"""
Moon Read Catalog Bot - Seenode Deployment
Bot: @MoonCatalogBot
Optimized for Seenode.com hosting
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import csv
import logging
import os
import random

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

# Load catalog data
BOOKS = []

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = f"""
🌙 **Welcome to Moon Read Catalog Bot!** 📚

Find novels from our collection of **{len(BOOKS)}+ EPUBs**!

**How to use:**

🔍 **Search for a book:**
`/search tempest`
Example: `/search villainess`

📖 **Random book:**
`/random`

📋 **Browse by alphabet:**
`/catalog` - Browse A-Z with buttons!

ℹ️ **Help:**
`/help`

Start searching now! 🚀
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
📚 **Moon Read Catalog Bot - Help**

**Available Commands:**

🔍 **Search:**
• `/search keyword` - Search for books
• Example: `/search romance`
• Example: `/search villainess tempest`

📋 **Browse:**
• `/catalog` - Browse with alphabet buttons! (NEW!)
• `/browse A` - Show all books starting with A
• `/browse #` - Show books starting with numbers

📖 **Random:**
• `/random` - Get a random book recommendation

📊 **Statistics:**
• `/stats` - Show catalog statistics

**Search Tips:**
• Search is case-insensitive
• Use multiple keywords: `/search fantasy romance`
• Partial matches work (e.g., "temp" finds "Tempest")

**Need help?** Contact @moonreadteam
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for books using /search command"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a search keyword!\n\n"
            "**Example:**\n"
            "`/search tempest`\n"
            "`/search villainess romance`",
            parse_mode='Markdown'
        )
        return
    
    keyword = ' '.join(context.args).lower()
    results = [book for book in BOOKS if keyword in book['title'].lower()]
    
    if not results:
        await update.message.reply_text(
            f"📭 No books found for: **{keyword}**\n\n"
            "Try different keywords!",
            parse_mode='Markdown'
        )
        return
    
    limited_results = results[:20]
    
    message = f"🔍 **Search Results for: {keyword}**\n\n"
    message += f"Found **{len(results)}** book(s)\n"
    if len(results) > 20:
        message += f"_(Showing first 20 results)_\n"
    message += "\n"
    
    for i, book in enumerate(limited_results, 1):
        message += f"{i}. [{book['title']}]({book['link']})\n\n"
    
    if len(results) > 20:
        message += f"_...and {len(results) - 20} more results_\n"
        message += f"\n💡 Tip: Use more specific keywords to narrow results"
    
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def random_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random book"""
    if not BOOKS:
        await update.message.reply_text("❌ Catalog not loaded. Please try again later.")
        return
    
    book = random.choice(BOOKS)
    
    message = f"""
📖 **Random Book Recommendation**

[{book['title']}]({book['link']})

Want another? Type `/random` again!
"""
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def browse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Browse books by first letter"""
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a letter!\n\n"
            "**Examples:**\n"
            "`/browse A` - Books starting with A\n"
            "`/browse #` - Books starting with numbers\n\n"
            "💡 **Tip:** Use `/catalog` to browse with buttons!",
            parse_mode='Markdown'
        )
        return
    
    letter = context.args[0].upper()
    
    # Filter books by first letter
    if letter == '#':
        filtered_books = [book for book in BOOKS if not book['title'][0].isalpha()]
    else:
        filtered_books = [book for book in BOOKS if book['title'][0].upper() == letter]
    
    if not filtered_books:
        await update.message.reply_text(
            f"📭 No books found starting with: **{letter}**",
            parse_mode='Markdown'
        )
        return
    
    # Limit to 30 books per message
    limited_books = filtered_books[:30]
    
    message = f"📚 **Books starting with '{letter}'**\n\n"
    message += f"Total: **{len(filtered_books)}** book(s)\n"
    if len(filtered_books) > 30:
        message += f"_(Showing first 30)_\n"
    message += "\n"
    
    for i, book in enumerate(limited_books, 1):
        message += f"{i}. [{book['title']}]({book['link']})\n\n"
    
    if len(filtered_books) > 30:
        message += f"_...and {len(filtered_books) - 30} more books_\n"
        message += f"\n💡 Use `/search {letter.lower()}` for better filtering"
    
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)


async def catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show alphabet keyboard for browsing"""
    
    # Count books by letter
    letter_counts = {}
    for book in BOOKS:
        first_char = book['title'][0].upper()
        letter = first_char if first_char.isalpha() else '#'
        letter_counts[letter] = letter_counts.get(letter, 0) + 1
    
    # Create inline keyboard with alphabet buttons (6 buttons per row)
    keyboard = []
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ#'
    
    row = []
    for letter in letters:
        count = letter_counts.get(letter, 0)
        if count > 0:  # Only show letters that have books
            button_text = f"{letter} ({count})"
            row.append(InlineKeyboardButton(button_text, callback_data=f"browse_{letter}"))
            
            if len(row) == 6 or letter == letters[-1]:  # 6 buttons per row
                keyboard.append(row)
                row = []
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"""
📚 **Moon Read Catalog - Browse by Letter**

Total Books: **{len(BOOKS)}**

Click any letter below to see books starting with that letter:
"""
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    # Extract letter from callback_data (format: "browse_A")
    action = query.data.split('_')
    if len(action) == 2 and action[0] == 'browse':
        letter = action[1]
        
        # Filter books by letter
        if letter == '#':
            filtered_books = [book for book in BOOKS if not book['title'][0].isalpha()]
        else:
            filtered_books = [book for book in BOOKS if book['title'][0].upper() == letter]
        
        if not filtered_books:
            await query.edit_message_text(
                f"📭 No books found starting with: **{letter}**",
                parse_mode='Markdown'
            )
            return
        
        # Limit to 30 books
        limited_books = filtered_books[:30]
        
        message = f"📚 **Books starting with '{letter}'**\n\n"
        message += f"Total: **{len(filtered_books)}** book(s)\n"
        if len(filtered_books) > 30:
            message += f"_(Showing first 30)_\n"
        message += "\n"
        
        for i, book in enumerate(limited_books, 1):
            message += f"{i}. [{book['title']}]({book['link']})\n\n"
        
        if len(filtered_books) > 30:
            message += f"_...and {len(filtered_books) - 30} more books_\n"
            message += f"\n💡 Use `/catalog` to browse other letters"
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            disable_web_page_preview=True
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
    
    message = f"📊 **Moon Read Catalog Statistics**\n\n"
    message += f"📚 **Total Books:** {len(BOOKS)}\n\n"
    message += f"🔤 **Books by Letter:**\n"
    
    # Show counts for each letter
    for letter in sorted(letter_counts.keys()):
        message += f"• {letter}: {letter_counts[letter]}\n"
    
    message += f"\n💡 Use `/browse <letter>` to see books for any letter!"
    
    await update.message.reply_text(message, parse_mode='Markdown')


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
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("random", random_book))
    application.add_handler(CommandHandler("browse", browse_command))
    application.add_handler(CommandHandler("catalog", catalog_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("\n" + "=" * 70)
    print("✅ Bot started successfully!")
    print("=" * 70)
    print("🔍 Search: /search keyword")
    print("📋 Catalog: /catalog (with buttons!)")
    print("📖 Random: /random")
    print("📊 Stats: /stats")
    print("=" * 70)
    print("\n🚀 Bot is running!\n")
    
    # Run bot (polling mode for Seenode)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
