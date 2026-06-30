import os
import sys
import logging
import io
import aiohttp
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
def get_token():
    """Get bot token from environment variables."""
    token = os.environ.get('BOT_TOKEN')
    if not token:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ No BOT_TOKEN found in environment variables!")
        logger.error("Please add BOT_TOKEN to your Railway Variables.")
        sys.exit(1)
    return token

TOKEN = get_token()
logger.info("✅ Bot token loaded successfully!")

# Store user settings
user_settings = {}

# Art styles with their prompts
STYLES = {
    'realistic': 'photorealistic, 8k, highly detailed, natural lighting, professional photography',
    'anime': 'anime style, studio ghibli inspired, vibrant colors, detailed, japanese animation',
    'digital_art': 'digital art, highly detailed, 4k, vibrant colors, concept art',
    'oil_painting': 'oil painting, renaissance style, textured, dramatic lighting, classical',
    'watercolor': 'watercolor painting, soft colors, artistic, dreamy, flowing',
    'cartoon': 'cartoon style, pixar inspired, colorful, playful, whimsical',
    'cyberpunk': 'cyberpunk style, neon lights, futuristic, dark atmosphere, sci-fi',
    'fantasy': 'fantasy art, magical, ethereal, detailed, mythical',
    'minimalist': 'minimalist, clean lines, simple, modern, geometric',
    'sketch': 'pencil sketch, black and white, artistic, detailed, hand-drawn',
    '3d_render': '3d render, blender, cinematic, realistic, ray tracing',
    'vintage': 'vintage style, retro, nostalgic, film grain, classic',
    'surreal': 'surreal art, dreamlike, impossible, imaginative, dali style',
    'pop_art': 'pop art, comic style, bold colors, andy warhol inspired',
    'steampunk': 'steampunk, victorian, gears, brass, steam powered, retro-futuristic'
}

# Image sizes
SIZES = {
    'square': '1024x1024',
    'portrait': '768x1024',
    'landscape': '1024x768',
    'wide': '1280x720'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message."""
    user = update.effective_user
    welcome_text = f"""
🎨 **Welcome to VisualCraft0Bot, {user.first_name}!**

I'm your AI image generator. Send me a text description, and I'll create an image for you!

**Commands:**
/start - Show this welcome message
/help - Show all commands
/style - Choose an art style
/size - Choose image size
/settings - View your current settings
/generate [prompt] - Generate an image

**Examples:**
`A cyberpunk cat wearing a VR headset`
`A majestic dragon flying over a futuristic city`
`A beautiful landscape with mountains and sunset`

💡 **Tip:** Be specific for better results!
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = """
🖼️ **How to generate an image:**

1️⃣ Send me any descriptive text
2️⃣ I'll generate an image based on your prompt
3️⃣ Get your image instantly!

**Commands:**
/start - Welcome message
/help - Show this help message
/style - Choose an art style
/size - Choose image size
/settings - View your current settings
/generate [prompt] - Generate with specific prompt

**Style Options (15 styles):**
• Realistic • Anime • Digital Art
• Oil Painting • Watercolor • Cartoon
• Cyberpunk • Fantasy • Minimalist
• Sketch • 3D Render • Vintage
• Surreal • Pop Art • Steampunk

**Size Options:**
• Square (1024x1024)
• Portrait (768x1024)
• Landscape (1024x768)
• Wide (1280x720)

💡 **Pro tip:** Use /style and /size to customize your images!
"""
    await update.message.reply_text(help_text)


async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show style selection menu."""
    keyboard = []
    row = []
    for idx, (style_key, style_desc) in enumerate(STYLES.items()):
        display_name = style_key.replace('_', ' ').title()
        row.append(InlineKeyboardButton(display_name, callback_data=f"style_{style_key}"))
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="style_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎨 **Select an art style:**\n\n"
        "Choose your preferred style for image generation.",
        reply_markup=reply_markup
    )


async def size_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show size selection menu."""
    keyboard = [
        [
            InlineKeyboardButton("⬜ Square (1024x1024)", callback_data="size_square"),
            InlineKeyboardButton("📱 Portrait (768x1024)", callback_data="size_portrait"),
        ],
        [
            InlineKeyboardButton("🖥️ Landscape (1024x768)", callback_data="size_landscape"),
            InlineKeyboardButton("📺 Wide (1280x720)", callback_data="size_wide"),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="size_cancel"),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📏 **Select image size:**\n\n"
        "Choose the dimensions for your generated image.",
        reply_markup=reply_markup
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user settings."""
    user_id = update.effective_user.id
    settings = user_settings.get(user_id, {})
    style = settings.get('style', 'digital_art')
    size = settings.get('size', 'square')
    
    style_display = style.replace('_', ' ').title()
    size_display = size.replace('_', ' ').title()
    size_dimensions = SIZES.get(size, '1024x1024')
    
    settings_text = f"""
⚙️ **Your Settings:**

🎨 Style: {style_display}
📏 Size: {size_display} ({size_dimensions})
🔄 Quality: Standard

**Commands:**
/style - Change art style
/size - Change image size
/help - Get more help
"""
    await update.message.reply_text(settings_text)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "style_cancel":
        await query.edit_message_text("❌ Style selection cancelled.")
        return
    
    if data == "size_cancel":
        await query.edit_message_text("❌ Size selection cancelled.")
        return
    
    if data.startswith("style_"):
        style_key = data.replace("style_", "")
        if style_key in STYLES:
            if user_id not in user_settings:
                user_settings[user_id] = {}
            user_settings[user_id]['style'] = style_key
            
            style_display = style_key.replace('_', ' ').title()
            await query.edit_message_text(
                f"✅ **Style set to: {style_display}**\n\n"
                f"Now send me a prompt to generate an image in this style!\n"
                f"Or use /generate [your prompt]"
            )
    
    if data.startswith("size_"):
        size_key = data.replace("size_", "")
        if size_key in SIZES:
            if user_id not in user_settings:
                user_settings[user_id] = {}
            user_settings[user_id]['size'] = size_key
            
            size_display = size_key.replace('_', ' ').title()
            size_dimensions = SIZES[size_key]
            await query.edit_message_text(
                f"✅ **Size set to: {size_display} ({size_dimensions})**\n\n"
                f"Now send me a prompt to generate an image with this size!"
            )


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /generate command."""
    prompt = ' '.join(context.args)
    
    if not prompt:
        await update.message.reply_text(
            "❌ Please provide a prompt!\n\n"
            "Example: `/generate A beautiful sunset over mountains`"
        )
        return
    
    await generate_image(update, context, prompt)


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str = None) -> None:
    """Generate an image from text prompt."""
    # If prompt not provided, use the message text
    if prompt is None:
        prompt = update.message.text
    
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Get user's preferences
    settings = user_settings.get(user_id, {})
    style = settings.get('style', 'digital_art')
    size = settings.get('size', 'square')
    size_dimensions = SIZES.get(size, '1024x1024')
    
    # Get style prompt
    style_prompt = STYLES.get(style, STYLES['digital_art'])
    
    # Combine prompt with style
    full_prompt = f"{prompt}, {style_prompt}"
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🎨 **Generating your image...**\n\n"
        f"📝 Prompt: `{prompt}`\n"
        f"🎭 Style: {style.replace('_', ' ').title()}\n"
        f"📏 Size: {size_dimensions}\n"
        f"⏳ This may take a moment..."
    )
    
    try:
        # Use Pollinations API (free, no API key required)
        encoded_prompt = full_prompt.replace(' ', '%20')
        width, height = size_dimensions.split('x')
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    
                    # Send the image back to the user
                    await update.message.reply_photo(
                        photo=io.BytesIO(image_data),
                        caption=f"✅ **Image Generated!**\n\n"
                                f"📝 Prompt: `{prompt}`\n"
                                f"🎭 Style: {style.replace('_', ' ').title()}\n"
                                f"📏 Size: {size_dimensions}"
                    )
                    await processing_msg.delete()
                else:
                    raise Exception(f"API returned status {response.status}")
                    
    except Exception as e:
        logger.error(f"Image generation failed for user {user.id}: {e}")
        await processing_msg.edit_text(
            f"❌ **Sorry, I couldn't generate your image.**\n\n"
            f"Error: {str(e)}\n\n"
            f"💡 **Tips:**\n"
            f"• Try a simpler prompt\n"
            f"• Check your internet connection\n"
            f"• Use /help for guidance"
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages that aren't commands."""
    # Check if it's a command (starts with /)
    if update.message.text.startswith('/'):
        return
    
    # Generate image from text
    await generate_image(update, context)


def main() -> None:
    """Start the bot."""
    try:
        # Create Application
        application = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("style", style_command))
        application.add_handler(CommandHandler("size", size_command))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CommandHandler("generate", generate_command))
        
        # Add callback handler for inline buttons
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Add message handler for text messages (not commands)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Start the Bot
        logger.info("🚀 VisualCraft0Bot started successfully!")
        logger.info("🎨 Press Ctrl+C to stop.")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
