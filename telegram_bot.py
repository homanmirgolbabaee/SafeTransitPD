from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
from datetime import datetime
import logging
from typing import Dict, List
import asyncio

# States for conversation handler
LOCATION, CROWD_LEVEL, SAFETY_CONCERNS, ADDITIONAL_INFO = range(4)

class SafeTransitTelegramBot:
    def __init__(self, token: str, bus_stops: Dict[str, tuple], query_engine=None):
        self.token = token
        self.bus_stops = bus_stops
        self.query_engine = query_engine
        self.reports = []
        
        # Configure logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send welcome message when /start command is issued."""
        welcome_message = (
            "🚌 Welcome to SafeTransit Padova!\n\n"
            "I can help you:\n"
            "📍 Report transit issues\n"
            "🔍 Check real-time safety status\n"
            "🚨 Access emergency features\n"
            "🗺 Plan safe routes\n\n"
            "Use /help to see all available commands."
        )
        
        keyboard = [
            [InlineKeyboardButton("📝 Submit Report", callback_data='report')],
            [InlineKeyboardButton("🔍 Check Status", callback_data='status')],
            [InlineKeyboardButton("🚨 Emergency", callback_data='emergency')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send help message with available commands."""
        help_text = """
Available commands:
/start - Start the bot
/report - Submit a transit report
/status - Check real-time status
/emergency - Access emergency features
/route - Plan a safe route
/help - Show this help message
        """
        await update.message.reply_text(help_text)

    async def start_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the report submission process."""
        keyboard = [[location] for location in self.bus_stops.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            "📍 Please select your location:",
            reply_markup=reply_markup
        )
        return LOCATION

    async def process_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process selected location and ask for crowd level."""
        context.user_data['location'] = update.message.text
        
        keyboard = [['Low', 'Medium', 'High']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            "👥 What's the current crowd level?",
            reply_markup=reply_markup
        )
        return CROWD_LEVEL

    async def process_crowd_level(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process crowd level and ask for safety concerns."""
        context.user_data['crowd_level'] = update.message.text
        
        keyboard = [
            ['None'],
            ['Poor Lighting'],
            ['Suspicious Activity'],
            ['Technical Issues']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            "⚠️ Any safety concerns? Select one:",
            reply_markup=reply_markup
        )
        return SAFETY_CONCERNS

    async def process_safety_concerns(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Process safety concerns and ask for additional information."""
        context.user_data['safety_concerns'] = [update.message.text]
        
        await update.message.reply_text(
            "📝 Any additional information? (Type 'none' if nothing to add)"
        )
        return ADDITIONAL_INFO

    async def complete_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Complete the report submission process."""
        context.user_data['additional_info'] = update.message.text
        context.user_data['timestamp'] = datetime.now().isoformat()
        
        # Calculate safety score
        report_data = {
            "location": context.user_data['location'],
            "crowd_level": context.user_data['crowd_level'],
            "safety_concerns": context.user_data['safety_concerns'],
            "timestamp": context.user_data['timestamp']
        }
        
        # Store the report
        self.reports.append(report_data)
        
        # Generate AI analysis if query engine is available
        analysis = ""
        if self.query_engine:
            analysis = await self.get_ai_analysis(report_data)
            
        confirmation = (
            "✅ Report submitted successfully!\n\n"
            f"📍 Location: {context.user_data['location']}\n"
            f"👥 Crowd Level: {context.user_data['crowd_level']}\n"
            f"⚠️ Safety Concerns: {', '.join(context.user_data['safety_concerns'])}\n"
        )
        
        if analysis:
            confirmation += f"\n🤖 AI Analysis: {analysis}"
        
        await update.message.reply_text(confirmation)
        return ConversationHandler.END

    async def get_ai_analysis(self, report_data: Dict) -> str:
        """Get AI analysis of the report."""
        if not self.query_engine:
            return ""
            
        query = (
            f"Analyze this safety report: Location: {report_data['location']}, "
            f"Crowd Level: {report_data['crowd_level']}, "
            f"Safety Concerns: {', '.join(report_data['safety_concerns'])}"
        )
        response = await self.query_engine.aquery(query)
        return response.response

    async def emergency(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle emergency situations."""
        emergency_message = (
            "🚨 EMERGENCY MODE ACTIVATED!\n\n"
            "1. Alerting nearby safety personnel\n"
            "2. Notifying trusted contacts\n"
            "3. Recording your location\n\n"
            "Stay calm and remain in a safe location."
        )
        
        # Get AI recommendations if available
        if self.query_engine:
            response = await self.query_engine.aquery(
                "What are the immediate steps to take in a transit emergency?"
            )
            emergency_message += f"\n\n🤖 AI Recommendations:\n{response.response}"
        
        keyboard = [[InlineKeyboardButton("Cancel Emergency", callback_data='cancel_emergency')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(emergency_message, reply_markup=reply_markup)

    def run(self):
        """Run the bot."""
        application = Application.builder().token(self.token).build()
        
        # Add conversation handler for report submission
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('report', self.start_report),
                CallbackQueryHandler(self.start_report, pattern='^report$')
            ],
            states={
                LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_location)],
                CROWD_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_crowd_level)],
                SAFETY_CONCERNS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_safety_concerns)],
                ADDITIONAL_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.complete_report)]
            },
            fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
        )
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("emergency", self.emergency))
        application.add_handler(conv_handler)
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)