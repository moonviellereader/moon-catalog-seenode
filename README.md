# Moon Read Catalog Bot

Telegram bot untuk katalog novel EPUB dari channel [@moon_read](https://t.me/moon_read)

## Features

- 🔍 **Search**: Cari novel berdasarkan kata kunci
- 📋 **Browse**: Lihat novel berdasarkan huruf awal (A-Z, #)
- 📖 **Random**: Rekomendasi novel acak
- 📊 **Statistics**: Statistik katalog

## Bot Commands

- `/start` - Mulai menggunakan bot
- `/help` - Bantuan penggunaan
- `/search <keyword>` - Cari novel
- `/browse <letter>` - Lihat novel berdasarkan huruf (A-Z atau #)
- `/random` - Novel acak
- `/stats` - Statistik katalog

## Deployment on Seenode

### Environment Variables Required:
- `BOT_TOKEN` - Token bot dari @BotFather

### Setup:
1. Fork/clone repository ini
2. Connect ke Seenode.com
3. Pilih repository
4. Set environment variable `BOT_TOKEN`
5. Deploy!

### Start Command:
```
python bot.py
```

## Catalog Update

Untuk update katalog:
1. Edit file `titles_and_links_alphabetical.csv`
2. Format: `title,link`
3. Push ke repository
4. Seenode akan auto-deploy

## Current Stats

- 📚 Total Books: 1000+
- 🔄 Auto-updating dari channel
- 🌐 24/7 uptime on Seenode

## Contact

Channel: [@moon_read](https://t.me/moon_read)
Team: [@moonreadteam](https://t.me/moonreadteam)
Bot: [@MoonCatalogBot](https://t.me/MoonCatalogBot)

---

Made with ❤️ for Moon Read community
