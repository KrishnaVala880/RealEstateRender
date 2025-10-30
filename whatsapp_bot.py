import os
import json
import time
import re
import logging
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ===== ENVIRONMENT VARIABLES =====
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
def check_new_bookings():
    """Check for new entries in the Google Sheet and send confirmation messages"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the site visits sheet
        sheet = client.open(SITE_VISITS_SHEET_NAME).sheet1
        
        # Get all records
        all_records = sheet.get_all_records()
        
        for record in all_records:
            # Check if this is a new record that hasn't been processed
            if record.get('Status') == 'New':
                phone = record.get('Phone')
                name = record.get('Name')
                date = record.get('Preferred Date')
                time = record.get('Preferred Time')
                unit = record.get('Unit Type')
                
                if phone:
                    # Format the confirmation message
                    message = f"""🎉 *Site Visit Booking Confirmed!*\n\nDear {name},\n\nYour site visit to Brookstone has been scheduled:\n📅 Date: {date}\n⏰ Time: {time}\n🏠 Unit Interest: {unit}\n\n📍 *Location:*\nBrookstone Show Flat\nB/S, Vaikunth Bungalows, Next to Oxygen Park\nDPS-Bopal Road, Shilaj, Ahmedabad - 380059\n\nOur team will be ready to welcome you! \n\nNeed to reschedule? Contact us at: +91 1234567890\n\nSee you soon! 🌟"""

                    # Send WhatsApp confirmation
                    if send_whatsapp_text(phone, message):
                        # Update status to confirmed
                        sheet.update_cell(all_records.index(record) + 2, 8, 'Confirmed')
        
        return True
    
    except Exception as e:
        logging.error(f"Error checking new bookings: {e}")
        return False
    except Exception as e:
        logging.error(f"Error marking message as read: {e}")


# ===== GOOGLE SHEETS FUNCTIONS =====
def verify_credentials():
    """Verify Google API credentials and permissions"""
    try:
        # Check if credentials file exists
        if not os.path.exists('credentials.json'):
            logging.error("credentials.json file not found!")
            return False
            
        # Verify calendar access
        scopes = os.getenv('GOOGLE_SCOPES', '').split()
        creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
        calendar_service = build('calendar', 'v3', credentials=creds)
        
        # Try to access the calendar
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        calendar_service.calendars().get(calendarId=calendar_id).execute()
        
        logging.info("✅ Google Calendar access verified successfully!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error verifying credentials: {str(e)}")
        return False

def add_to_calendar(name, date_str, time_str, unit_type):
    """Add a site visit to Google Calendar"""
    try:
        # First verify credentials
        if not verify_credentials():
            logging.error("Failed to verify Google credentials")
            return False
            
        # Parse date and time
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        time_obj = datetime.strptime(time_str, "%I:%M %p")
        
        # Combine date and time
        start_time = date_obj.replace(
            hour=time_obj.hour,
            minute=time_obj.minute,
            tzinfo=pytz.timezone('Asia/Kolkata')
        )
        
        # Event ends after 1 hour
        end_time = start_time + timedelta(hours=1)
        
        # Set up calendar service
        scopes = os.getenv('GOOGLE_SCOPES', '').split()
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
        service = build('calendar', 'v3', credentials=creds)
        
        event = {
            'summary': f'Brookstone Site Visit - {name} ({unit_type})',
            'location': 'Brookstone Show Flat, B/S, Vaikunth Bungalows, Next to Oxygen Park, DPS-Bopal Road, Shilaj, Ahmedabad - 380059',
            'description': f'Site visit appointment for {name}\nUnit Interest: {unit_type}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': True
            }
        }
        
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        logging.info(f'Calendar event created: {event.get("htmlLink")}')
        return True
        
    except Exception as e:
        logging.error(f"Error creating calendar event: {e}")
        return False

def check_new_bookings():
    """Check for new entries in the Google Sheet and send confirmation messages"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Open the site visits sheet
        sheet = client.open(SITE_VISITS_SHEET_NAME).sheet1
        
        # Get all records
        all_records = sheet.get_all_records()
        
        for record in all_records:
            # Check if this is a new record that hasn't been processed
            if record.get('Status') == 'New':
                phone = record.get('Phone')
                name = record.get('Name')
                date = record.get('Preferred Date')
                time = record.get('Preferred Time')
                unit = record.get('Unit Type')
                
                if phone:
                    # Add to Google Calendar
                    calendar_added = add_to_calendar(name, date, time, unit)
                    
                    # Format the confirmation message
                    message = f"""🎉 *Site Visit Booking Confirmed!*

Dear {name},

Your site visit to Brookstone has been scheduled:
📅 Date: {date}
⏰ Time: {time}
🏠 Unit Interest: {unit}

📍 *Location:*
Brookstone Show Flat
B/S, Vaikunth Bungalows, Next to Oxygen Park
DPS-Bopal Road, Shilaj, Ahmedabad - 380059

Our team will be ready to welcome you! 

Need to reschedule? Contact us at: +91 1234567890

See you soon! 🌟"""

                    # Send WhatsApp confirmation
                    if send_whatsapp_text(phone, message):
                        # Update status to confirmed
                        status = 'Confirmed' if calendar_added else 'Confirmed (Calendar Failed)'
                        sheet.update_cell(all_records.index(record) + 2, 8, status)
        
        return True
    
    except Exception as e:
        logging.error(f"Error checking new bookings: {e}")
        return False


def extract_budget_from_text(text):
    """Extract budget information from user text"""
    patterns = [
        r'(\d+\.?\d*)\s*(?:cr|crore|crores)',
        r'(\d+\.?\d*)\s*(?:lakh|lakhs)',
        r'₹\s*(\d+\.?\d*)\s*(?:cr|crore|crores)',
        r'₹\s*(\d+\.?\d*)\s*(?:lakh|lakhs)',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = float(match.group(1))
            if 'cr' in pattern or 'crore' in pattern:
                return f"{amount} Cr"
            elif 'lakh' in pattern:
                return f"{amount} Lakh"
    
    return None


# ===== GEMINI AI LOGIC (from appq_gemini.py) =====
def extract_relevant_data(user_question, faq_data, language='english'):
    """Extract only relevant data based on user question to reduce API payload"""
    lang_data = faq_data.get(language, faq_data.get('english', {}))
    relevant_data = {}
    user_question_lower = user_question.lower()
    
    # Always include basic project info
    if 'project_info' in lang_data:
        relevant_data['project_info'] = lang_data['project_info']
    
    # Check for various topics
    if any(word in user_question_lower for word in ['price', 'cost', 'bhk', 'bedroom', 'size', 'sqft', 'configuration', 'apartment']):
        if 'unit_configurations' in lang_data:
            relevant_data['unit_configurations'] = lang_data['unit_configurations']
        if 'pricing' in lang_data:
            relevant_data['pricing'] = lang_data['pricing']
    
    if any(word in user_question_lower for word in ['kitchen', 'room', 'bedroom', 'living', 'dining', 'bathroom', 'toilet', 'balcony']):
        if '3bhk_unit_plan' in lang_data:
            relevant_data['3bhk_unit_plan'] = lang_data['3bhk_unit_plan']
        if '4bhk_unit_plan' in lang_data:
            relevant_data['4bhk_unit_plan'] = lang_data['4bhk_unit_plan']

    # Ground floor / floor plan queries
    if any(word in user_question_lower for word in ['ground', 'ground floor', 'floor plan', 'groundfloor', 'ground-floor']):
        if 'ground_floor_plan' in lang_data:
            relevant_data['ground_floor_plan'] = lang_data['ground_floor_plan']
    
    if any(word in user_question_lower for word in ['amenity', 'amenities', 'facility', 'gym', 'pool', 'park', 'club']):
        if 'amenities' in lang_data:
            relevant_data['amenities'] = lang_data['amenities']
    
    if any(word in user_question_lower for word in ['location', 'address', 'connectivity', 'metro', 'nearby', 'landmark']):
        if 'location_details' in lang_data:
            relevant_data['location_details'] = lang_data['location_details']
    
    if any(word in user_question_lower for word in ['possession', 'ready', 'completion', 'timeline', 'delivery']):
        if 'possession_details' in lang_data:
            relevant_data['possession_details'] = lang_data['possession_details']
    
    if any(word in user_question_lower for word in ['developer', 'shatranj', 'aarat', 'group', 'company', 'builder']):
        if 'developer_portfolio' in lang_data:
            relevant_data['developer_portfolio'] = lang_data['developer_portfolio']
    
    # If minimal data, add more sections
    if len(relevant_data) <= 2:
        for section in ['unit_configurations', 'pricing', '3bhk_unit_plan', '4bhk_unit_plan', 'amenities', 'location_details']:
            if section in lang_data:
                relevant_data[section] = lang_data[section]
    
    return relevant_data


def create_gemini_prompt(user_question, faq_data, language='english', chat_history=None):
    """Create an optimized prompt for Gemini with only relevant data and conversation context"""
    relevant_data = extract_relevant_data(user_question, faq_data, language)
    
    # Build conversation context
    conversation_context = ""
    if chat_history and len(chat_history) > 0:
        recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
        conversation_context = "\n\nRECENT CONVERSATION:\n"
        for msg, is_user in recent_history:
            role = "User" if is_user else "Bot"
            conversation_context += f"{role}: {msg}\n"
    
    prompt = f"""
You are a helpful real estate chatbot for the Brookstone project. Answer user questions based on the provided project data and conversation context.

PROJECT DATA:
{json.dumps(relevant_data, indent=2)}{conversation_context}

USER QUESTION: {user_question}

INSTRUCTIONS:
1. ALWAYS use the PROJECT DATA provided above to answer questions
2. Consider the RECENT CONVERSATION context - if user says "yes", "sure", "please", they are responding to your previous question
3. If any detail shows "TBD", say "This detail is yet to be finalized"
4. Keep responses concise but comprehensive (max 1000 characters for WhatsApp)
5. Possession is May 2027
6. After answering, ask 1 natural follow-up question to keep conversation going
7. Be conversational and friendly like a real sales agent
8. NEVER suggest WhatsApp links - only provide phone numbers
9. For agent contact, ONLY provide phone number +91 1234567890
10. Format your response for WhatsApp - use emojis and clear structure

ANSWER:"""
    
    return prompt


def call_gemini_api(prompt, language='english'):
    """Call Google Gemini API with retry logic"""
    if not GEMINI_API_KEY:
        return "⚠️ Please configure your Gemini API key"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 800
        }
    }
    
    for attempt in range(2):
        try:
            if attempt > 0:
                time.sleep(2)
            
            response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        return candidate['content']['parts'][0]['text']
            
            logging.warning(f"Gemini API error: {response.status_code}")
                    
        except Exception as e:
            logging.error(f"Gemini API exception: {e}")
            continue
    
    return "Sorry, I'm having trouble answering right now. Please try again or contact our agent at +91 1234567890."


# ===== MESSAGE PROCESSING LOGIC =====
def process_incoming_message(from_phone, message_text, message_id):
    """Process incoming WhatsApp message and generate response"""
    
    # Get or create user state
    if from_phone not in CONV_STATE:
        CONV_STATE[from_phone] = {
            'chat_history': [],
            'lead_capture_mode': None,
            'user_phone': from_phone,
            'language': 'english',
            'asked_about_brochure': False,
            'booking_info': {}
        }
    
    state = CONV_STATE[from_phone]
    user_lower = message_text.lower().strip()
    
    # Detect language from user's message
    detected_lang = detect_language(message_text)
    state['language'] = detected_lang  # Update user's preferred language
    
    # Add user message to history
    state['chat_history'].append((message_text, True))
    
    # ===== HANDLE PHONE NUMBER FOR BROCHURE =====
    if state.get('lead_capture_mode') == 'phone_for_brochure':
        phone_pattern = r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b'
        phone_match = re.search(phone_pattern, message_text)
        
        if phone_match:
            phone_number = phone_match.group().replace(' ', '').replace('-', '')
            state['user_phone'] = phone_number
            state['lead_capture_mode'] = None
            
            success = send_whatsapp_document(phone_number, BROCHURE_MEDIA_ID)
            
            if not success:
                reply = """I apologize, but there was an issue sending the brochure to your WhatsApp. 

Please try again later or contact our agent directly at +91 1234567890."""
                state['chat_history'].append((reply, False))
                return reply
                
            return None
        else:
            reply = """I didn't find a valid phone number. Please share your *10-digit mobile number* to send the brochure.

For example: 9876543210 or +91 9876543210"""
            state['chat_history'].append((reply, False))
            return reply
    
    # ===== DETECT BROCHURE REQUEST =====
    brochure_keywords = ['brochure', 'pdf', 'download', 'send brochure', 'share brochure', 'floor plan', 'send pdf']
    if any(kw in user_lower for kw in brochure_keywords):
        state['asked_about_brochure'] = True
        
        # Send brochure directly to the phone number that messaged us
        success = send_whatsapp_document(from_phone, BROCHURE_MEDIA_ID)
        
        if not success:
            reply = """I apologize, but there was an issue sending the brochure.

Please contact our agent at +91 1234567890 for assistance."""
            state['chat_history'].append((reply, False))
            return reply
            
        return None
    
    # ===== HANDLE AFFIRMATIVE RESPONSE TO BROCHURE =====
    if state.get('asked_about_brochure', False):
        state['asked_about_brochure'] = False
        
        affirmative_patterns = ['yes', 'yeah', 'yup', 'sure', 'ok', 'okay', 'please', 'send', 'want', 'need']
        
        if any(a in user_lower for a in affirmative_patterns):
            success = send_whatsapp_document(from_phone, BROCHURE_MEDIA_ID)
            
            if not success:
                reply = """❌ There was an issue sending your brochure on WhatsApp.
Please contact our agent at +91 1234567890."""
                state['chat_history'].append((reply, False))
                return reply
                
            return None
    
    # ===== HANDLE WHATSAPP CONTACT REQUEST =====
    contact_patterns = ['whatsapp chat', 'whatsapp number', 'agent whatsapp', 'contact agent', 'agent contact', 'talk to agent']
    
    if any(phrase in user_lower for phrase in contact_patterns):
        reply = f"""Great! You can reach our agent, Shatranj, directly on WhatsApp at:

📱 *WhatsApp Number:* +91 1234567890

Our team will respond within 30 minutes during office hours (10 AM - 7 PM).

You can also call on the same number for a phone conversation.

Is there anything else about Brookstone I can help you with? 🏠"""
        
        state['chat_history'].append((reply, False))
        return reply
    
    # ===== HANDLE SITE VISIT BOOKING =====
    booking_keywords = ['book site visit', 'schedule visit', 'site visit', 'book appointment', 'visit booking']
    
    if any(kw in user_lower for kw in booking_keywords):
        google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSceds-nIr9vTLHJ0Jl1TOv0DNYGQhb0CtEa2R3mA9Ae3iP8Lg/viewform"
        
        reply = f"""🏠 *Book Your Site Visit to Brookstone*

To schedule your site visit, please click the link below and fill out a quick form:

📝 {google_form_url}

The form will ask for:
• Your Name
• Contact Number
• Preferred Date & Time
• Unit Type Interest
• Budget Range

Once you submit the form, our team will confirm your appointment within 2 hours.

Need help with the form? Feel free to ask! 😊"""
        
        state['chat_history'].append((reply, False))
        return reply
        
        state['chat_history'].append((reply, False))
        return reply
    
    # ===== HANDLE BOOKING FORM SUBMISSION =====
    if state.get('lead_capture_mode') == 'booking':
        booking_info = state['booking_info']
        current_step = booking_info.get('current_step')
        
        if current_step == 'name':
            booking_info['name'] = message_text
            booking_info['current_step'] = 'confirm_phone'
            
            reply = f"""Thank you, {message_text}! 📝

I have your phone number as: *{from_phone}*
Is this the correct number for the site visit coordination?

Reply with:
1️⃣ *Yes* to confirm this number
2️⃣ Or type your *alternate number*"""
            
            state['chat_history'].append((reply, False))
            return reply
            
        elif current_step == 'confirm_phone':
            if user_lower == 'yes' or user_lower == '1':
                phone = booking_info['phone']
            else:
                # Check if valid phone number provided
                phone_pattern = r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b'
                phone_match = re.search(phone_pattern, message_text)
                if phone_match:
                    phone = phone_match.group().replace(' ', '').replace('-', '')
                else:
                    reply = """Please provide a valid 10-digit phone number or type *Yes* to confirm the existing number.

Example: 9876543210 or +91 9876543210"""
                    state['chat_history'].append((reply, False))
                    return reply
            
            booking_info['phone'] = phone
            booking_info['current_step'] = 'date'
            
            reply = """Great! Now, please tell me your *preferred date* for the site visit.

Format: DD/MM/YYYY
Example: 05/11/2025"""
            
            state['chat_history'].append((reply, False))
            return reply
            
        elif current_step == 'date':
            # Basic date validation
            date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{4}'
            if not re.match(date_pattern, message_text):
                reply = """Please provide the date in the correct format (DD/MM/YYYY).

Example: 05/11/2025"""
                state['chat_history'].append((reply, False))
                return reply
            
            booking_info['date'] = message_text
            booking_info['current_step'] = 'time'
            
            reply = """Perfect! Now, please select your *preferred time* for the site visit.

Available slots:
1️⃣ 10:00 AM
2️⃣ 11:30 AM
3️⃣ 02:00 PM
4️⃣ 03:30 PM
5️⃣ 05:00 PM

Reply with the slot number (1-5) or type the time."""
            
            state['chat_history'].append((reply, False))
            return reply
            
        elif current_step == 'time':
            time_slots = {
                '1': '10:00 AM',
                '2': '11:30 AM',
                '3': '02:00 PM',
                '4': '03:30 PM',
                '5': '05:00 PM'
            }
            
            if message_text in time_slots:
                time_slot = time_slots[message_text]
            else:
                time_slot = message_text
            
            booking_info['time'] = time_slot
            booking_info['current_step'] = 'unit_type'
            
            reply = """Excellent! Which unit type are you interested in?

1️⃣ *3 BHK* (2650 sq ft)
2️⃣ *4 BHK* (3850 sq ft)
3️⃣ *Both options*

Please reply with 1, 2, or 3."""
            
            state['chat_history'].append((reply, False))
            return reply
            
        elif current_step == 'unit_type':
            unit_types = {
                '1': '3 BHK',
                '2': '4 BHK',
                '3': 'Both 3 & 4 BHK'
            }
            
            if message_text not in ['1', '2', '3']:
                reply = """Please select a valid option:
1️⃣ for 3 BHK
2️⃣ for 4 BHK
3️⃣ for Both options"""
                state['chat_history'].append((reply, False))
                return reply
            
            booking_info['unit_type'] = unit_types[message_text]
            booking_info['current_step'] = 'budget'
            
            reply = """Almost done! 🎯

What is your *approximate budget*?

Example formats:
• 1.5 Cr
• 2 Crore
• 150 Lakhs"""
            
            state['chat_history'].append((reply, False))
            return reply
            
        elif current_step == 'budget':
            budget = extract_budget_from_text(message_text)
            if not budget:
                reply = """Please specify your budget in a clear format:
Example: 1.5 Cr, 2 Crore, or 150 Lakhs"""
                state['chat_history'].append((reply, False))
                return reply
            
            booking_info['budget'] = budget
            
            # Since we're using Google Forms now, redirect to form
            google_form_url = "https://docs.google.com/forms/d/e/1FAIpQLSceds-nIr9vTLHJ0Jl1TOv0DNYGQhb0CtEa2R3mA9Ae3iP8Lg/viewform"
            
            # Clear booking mode
            state['lead_capture_mode'] = None
            
            reply = f"""� To complete your booking, please fill out our site visit form:

📝 {google_form_url}

Once you submit the form, you'll receive a confirmation message with all the details.

Need help with anything else? �"""
            
            state['asked_about_brochure'] = True
            state['chat_history'].append((reply, False))
            return reply
    
    # ===== EXTRACT AND SAVE BUDGET =====
    budget = extract_budget_from_text(message_text)
    if budget and state.get('booking_info'):
        # Since we're now using Google Forms to collect budget
        # Simply log for tracking
        logging.info(f"Budget indicated by {from_phone}: {budget}")
    
    # ===== DEFAULT: USE GEMINI FOR GENERAL QUESTIONS =====
    chat_history = state.get('chat_history', [])
    prompt = create_gemini_prompt(message_text, FAQ_DATA, state['language'], chat_history)
    ai_response = call_gemini_api(prompt, state['language'])
    
    state['chat_history'].append((ai_response, False))
    return ai_response


# ===== WEBHOOK ROUTES =====
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Webhook verification endpoint for Meta"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    logging.info(f"Webhook verification: mode={mode}, token={token}")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logging.info('✅ WEBHOOK VERIFIED')
        return challenge, 200
    else:
        logging.warning('❌ WEBHOOK VERIFICATION FAILED')
        return 'Forbidden', 403


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint to receive messages from WhatsApp"""
    data = request.get_json()
    
    logging.info(f"Incoming webhook: {json.dumps(data, indent=2)[:500]}...")
    
    try:
        # Parse WhatsApp Cloud API webhook structure
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                
                # Get messages
                messages = value.get('messages', [])
                for message in messages:
                    from_phone = message.get('from')
                    message_id = message.get('id')
                    msg_type = message.get('type')
                    
                    text = ''
                    
                    if msg_type == 'text':
                        text = message.get('text', {}).get('body', '')
                    elif msg_type == 'button':
                        text = message.get('button', {}).get('text', '')
                    elif msg_type == 'interactive':
                        interactive = message.get('interactive', {})
                        if 'button_reply' in interactive:
                            text = interactive['button_reply'].get('title', '')
                        elif 'list_reply' in interactive:
                            text = interactive['list_reply'].get('title', '')
                    
                    if not text:
                        logging.warning(f"No text found in message type: {msg_type}")
                        continue
                    
                    logging.info(f"📱 Message from {from_phone}: {text}")
                    
                    # Mark message as read
                    mark_message_as_read(message_id)
                    
                    # Process the message and get response
                    response_text = process_incoming_message(from_phone, text, message_id)
                    
                    # Send response back
                    send_whatsapp_text(from_phone, response_text)
    
    except Exception as e:
        logging.exception('❌ Error processing webhook')
    
    return jsonify({'status': 'ok'}), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'whatsapp_configured': bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID),
        'gemini_configured': bool(GEMINI_API_KEY)
    }), 200


@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Brookstone WhatsApp Bot is running!',
        'endpoints': {
            'webhook': '/webhook',
            'health': '/health'
        }
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logging.info(f"🚀 Starting Brookstone WhatsApp Bot on port {port}")
    logging.info(f"WhatsApp configured: {bool(WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID)}")
    logging.info(f"Gemini configured: {bool(GEMINI_API_KEY)}")
    app.run(host='0.0.0.0', port=port, debug=False)
