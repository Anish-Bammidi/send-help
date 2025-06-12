import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Admin SDK Service Account Key
SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "restaurant-data-backend",
    "private_key_id": "fdf27bcbb8e2ab65fe5ed4f812478f550ca7a40a",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDNYUFVRchSeS65\nwp7vh62xYdX7SZuDplUWZtEyywB8i/lSB5btHMrVkW5d/810qVrxBY7fkqYlqvRH\nRqXOtwOPG72vZbO5q3TH9GI8uhaMoW92tpTIc0umlzG0Z8Uf1djkSBfydwsSUuye\nt9P6MYi+iz1zI6nalSdxSgenRir/jLMDtP3+FDksLOaHja9g2eWT8YfnnP/mdb5J\nI20dLtvuPwyE9dOMMVAI7/FJ0nVF3dnWmKIwf9kMWdX/vQPEdNzfZTzFsy0+335H\nw6SbNhpVWrZcxMIb7E7MUp26VJw0MofiIuPlZwA+9ICQajTUnyriyBv0heYjlr/k\noeRl4g+lAgMBAAECggEAJlAlCbUPonEIWi94Ckunh55udmb8G6JRH7F1B7JuiA1t\nqJORYHDdVtt/OQpiB8gbFrjYdxUqqP67/LrtbgNeptkAOQLyNOoLCk0o8Vauo7Pu\n8PitBzrY6z4rz9GG6MIyKJ3ZV8pE1rmA+jflU7hfX9pmT38g7c2i0sPCaz5QAaVm\nLoKtRbdCgsnfbCvic+nd7m4x1sFxljUG9bjag3821qWbv8YHz1IqVhKma4y7DRbv\nStxGiV+XH8K9AD8f9caQFsBfPEvovPiZhsBqbF7DM/psQ8QkTgICrs6zb6pOZyUi\ndpbq5oal0ynVZpYXkC/2LPnpETP+3qcPRaz4DXuluQKBgQD2e8aC9Q8JTVmJ7RdE\nXP8KBForSDA3tZ0fLGxTJH286bhzUVlsUg9AFaGpgzOS3BGfzk4wfZ/g58/9kbyt\niGH/yi0RMyrrO9wwY4UoRaNC2AkgtZt1JhOPIChrMGW2dIsVq+I8VPkbqUtgl+bd\n5MrN0Qz7MgoGEbOWsfAoMR8uGQKBgQDVTzcDmAZ5qkUoY9idtABCOdDIUgbmPFbr\nWOuCAxVh7AhzfgC44igZm+T97x/xP1Pj7w6wwTCF9T/rKQo7TFaAMGeih+hfz6GI\ncPf2m/UhO6vGqF9etA8VHp3p+eAc4L4obAcHjTbMmOR4l99hgWD9giHFpQwH94FS\nt0hmYbbHbQKBgGl95iNMYOgZS9YlPA0NRDZ0UGcv2TsuppWd/KrE9m+xFDl+uqgK\nou5Jk8wqFBupxn0/3eURDylB7ZnYEwmuUksYq5st7BOLphyrq2TmEQ7dyWJPd752\n0m4yVDo0F4Q0cwaObyBlOcyl81XfDXcwob/e1hB4hSO91cAMXf3FsFOZAoGAI9x/\neUEzxXyUx+eRYWIDsR6bNTJlKov2aPa4EVGHZMET4qbKZErRRwzogLCVBDALYISu\nSZURHVRP/K8Xo0SAPmjk43RJ4uG7XH7xkSpDGeU4SdvAvOE0r+5HyjBSN0ipb45J\n2EErd1Y1Avk1euUPc09PcjT/Qs+flFJv/5Zp7jkCgYEAhtTs0gnnRv694Doss/KB\nxgECRq+Z/rfeYnLTFCy/5JTequs1C8rJFEkJMGXMhQz1oVgLRuMz3g8ZVuUsFi4R\nj0cZkXVAmDUKdu4AUrGi9odPewndE922bx/74FU3RXXoWhtQf7biRtAinm7NjD12\nPph4hjoK6uO6dAMDIZ3RsGY=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@restaurant-data-backend.iam.gserviceaccount.com",
    "client_id": "115855681795792637429",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40restaurant-data-backend.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# GEMINI AI API KEY
GEMINI_API_KEY = "AIzaSyAdOsM8ZyjaclxIzy29AdPLLop-NOH4GLw"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Initialize Firebase Admin SDK
@st.cache_resource
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        return None

# Get Firestore client
db = initialize_firebase()

# Firebase Helper Functions (Using Admin SDK)
def get_collection(collection_name):
    """Fetch all documents from a collection using Firebase Admin SDK"""
    try:
        if not db:
            return {}
        
        docs = db.collection(collection_name).stream()
        documents = {}
        
        for doc in docs:
            documents[doc.id] = doc.to_dict()
        
        return documents
    except Exception as e:
        st.error(f"Error fetching {collection_name}: {e}")
        return {}

def add_document(collection_name, doc_id, data):
    """Add a document to a collection using Firebase Admin SDK"""
    try:
        if not db:
            return False
        
        db.collection(collection_name).document(doc_id).set(data)
        return True
    except Exception as e:
        st.error(f"Error adding document to {collection_name}: {e}")
        return False

def call_gemini_ai_direct(user_message, ingredients_data, menu_data):
    """Call Gemini AI DIRECTLY with user input - NO RULE-BASED LOGIC"""
    try:
        # Build the context with restaurant data
        context = f"""You are EventBot, an AI assistant for a restaurant. Here's the current restaurant data:

INGREDIENTS ({len(ingredients_data)} items):
"""
        
        # Add all ingredient data
        for name, data in ingredients_data.items():
            context += f"- {name}: {data.get('Quantity', 'Unknown')} (expires: {data.get('Expiry', 'Unknown')}, type: {data.get('Type', 'Unknown')}, alternatives: {data.get('Alternatives', 'None')})\n"
        
        context += f"\nMENU ITEMS ({len(menu_data)} dishes):\n"
        
        # Add all menu data
        for item_id, item in menu_data.items():
            context += f"- {item.get('name', 'Unnamed')}: {item.get('description', 'No description')} (Category: {item.get('category', 'Unknown')}, Ingredients: {', '.join(item.get('ingredients', []))}, Tags: {', '.join(item.get('tags', []))})\n"
        
        # Add today's date for context
        context += f"\nToday's date: {datetime.now().date()}\n\n"
        
        # Add the user's EXACT question with NO preprocessing
        context += f"User question: {user_message}\n\nPlease respond naturally and helpfully based on the restaurant data above."

        # Prepare the API request for Gemini
        payload = {
            "contents": [{
                "parts": [{
                    "text": context
                }]
            }],
            "generationConfig": {
                "temperature": 0.9,  # High creativity
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the API call to Gemini
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                return ai_response
            else:
                return "I'm sorry, I couldn't generate a response right now. Please try asking your question differently! 🤖"
        else:
            return f"❌ API Error {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        return "⏰ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "🌐 Connection error. Please check your internet connection."
    except Exception as e:
        return f"🚨 Unexpected error: {str(e)}"

def create_sample_data():
    """Create sample data for testing"""
    # Sample ingredients
    sample_ingredients = {
        "tomatoes": {"Quantity": "5 kg", "Expiry": "2024-12-20", "Type": "vegetarian", "Alternatives": "cherry tomatoes, canned tomatoes"},
        "chicken_breast": {"Quantity": "3 kg", "Expiry": "2024-12-18", "Type": "mixed", "Alternatives": "chicken thigh, turkey breast"},
        "rice": {"Quantity": "10 kg", "Expiry": "2025-06-15", "Type": "vegan", "Alternatives": "quinoa, pasta"},
        "cheese": {"Quantity": "2 kg", "Expiry": "2024-12-25", "Type": "vegetarian", "Alternatives": "vegan cheese, nutritional yeast"},
        "lettuce": {"Quantity": "1 kg", "Expiry": "2024-12-16", "Type": "vegan", "Alternatives": "spinach, arugula"},
        "olive_oil": {"Quantity": "2 L", "Expiry": "2025-03-01", "Type": "vegan", "Alternatives": "vegetable oil, coconut oil"},
        "onions": {"Quantity": "3 kg", "Expiry": "2025-01-10", "Type": "vegan", "Alternatives": "shallots, leeks"},
        "garlic": {"Quantity": "500 g", "Expiry": "2025-01-05", "Type": "vegan", "Alternatives": "garlic powder, shallots"},
        "pasta": {"Quantity": "5 kg", "Expiry": "2025-08-01", "Type": "vegan", "Alternatives": "rice, quinoa"},
        "milk": {"Quantity": "2 L", "Expiry": "2024-12-17", "Type": "vegetarian", "Alternatives": "almond milk, oat milk"}
    }
    
    # Sample menu items
    sample_menu = {
        "caesar_salad": {
            "name": "Caesar Salad",
            "description": "Fresh romaine lettuce with parmesan cheese, croutons and caesar dressing",
            "category": "Starter",
            "ingredients": ["lettuce", "cheese", "olive_oil"],
            "tags": ["vegetarian"]
        },
        "chicken_pasta": {
            "name": "Chicken Alfredo Pasta",
            "description": "Creamy pasta with grilled chicken breast and parmesan cheese",
            "category": "Main",
            "ingredients": ["pasta", "chicken_breast", "cheese", "garlic"],
            "tags": ["gluten-free"]
        },
        "tomato_rice": {
            "name": "Tomato Rice",
            "description": "Aromatic rice cooked with fresh tomatoes and herbs",
            "category": "Main",
            "ingredients": ["rice", "tomatoes", "onions", "garlic", "olive_oil"],
            "tags": ["vegan", "gluten-free"]
        },
        "cheese_omelette": {
            "name": "Cheese Omelette",
            "description": "Fluffy omelette filled with melted cheese",
            "category": "Main",
            "ingredients": ["cheese", "milk"],
            "tags": ["vegetarian"]
        }
    }
    
    return sample_ingredients, sample_menu

# Streamlit App Configuration
st.set_page_config(
    page_title="EventBot - Restaurant Event Planning",
    page_icon="🍽️",
    layout="wide"
)

# App Header
st.title("🍽️ EventBot - Restaurant Event Planning System")
st.markdown("---")

# Firebase Connection Status
if db:
    st.sidebar.success("🔥 Firebase Admin SDK Connected!")
else:
    st.sidebar.error("❌ Firebase Connection Failed")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a section:",
    ["Dashboard", "Ingredient Inventory", "Menu Management", "Event Planning", "EventBot AI Chat"]
)

# Helper Functions
def get_ingredient_inventory():
    """Fetch all ingredients from Firestore"""
    return get_collection('ingredient_inventory')

def get_menu_items():
    """Fetch all menu items from Firestore"""
    return get_collection('menu')

def add_ingredient(name, quantity, expiry, ingredient_type, alternatives):
    """Add new ingredient to inventory"""
    data = {
        'Quantity': quantity,
        'Expiry': expiry,
        'Type': ingredient_type,
        'Alternatives': alternatives
    }
    return add_document('ingredient_inventory', name, data)

def add_menu_item(item_id, name, description, category, ingredients, tags):
    """Add new menu item"""
    data = {
        'name': name,
        'description': description,
        'category': category,
        'ingredients': ingredients,
        'tags': tags
    }
    return add_document('menu', item_id, data)

# Dashboard Page
if page == "Dashboard":
    st.header("📊 Dashboard")
    
    # Add sample data button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Add Sample Data for Testing", type="primary"):
            sample_ingredients, sample_menu = create_sample_data()
            
            # Add sample ingredients
            success_count = 0
            for name, data in sample_ingredients.items():
                if add_ingredient(name, data['Quantity'], data['Expiry'], data['Type'], data['Alternatives']):
                    success_count += 1
            
            # Add sample menu items
            for item_id, data in sample_menu.items():
                if add_menu_item(item_id, data['name'], data['description'], data['category'], data['ingredients'], data['tags']):
                    success_count += 1
            
            st.success(f"✅ Added {success_count} items! Refresh the page to see the data.")
            st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Inventory Overview")
        ingredients = get_ingredient_inventory()
        
        if ingredients:
            st.metric("Total Ingredients", len(ingredients))
            
            # Check for expiring ingredients
            today = datetime.now().date()
            expiring_soon = []
            
            for name, data in ingredients.items():
                try:
                    expiry_date = datetime.strptime(data.get('Expiry', ''), '%Y-%m-%d').date()
                    days_until_expiry = (expiry_date - today).days
                    if days_until_expiry <= 7:
                        expiring_soon.append((name, days_until_expiry))
                except:
                    continue
            
            if expiring_soon:
                st.warning(f"⚠️ {len(expiring_soon)} ingredients expiring within 7 days")
                for name, days in expiring_soon:
                    if days < 0:
                        st.write(f"• {name}: EXPIRED ({abs(days)} days ago)")
                    else:
                        st.write(f"• {name}: {days} days remaining")
            else:
                st.success("✅ No ingredients expiring soon")
        else:
            st.info("No ingredients found in inventory. Click 'Add Sample Data' to get started!")
    
    with col2:
        st.subheader("🍽️ Menu Overview")
        menu_items = get_menu_items()
        
        if menu_items:
            st.metric("Total Menu Items", len(menu_items))
            
            # Category breakdown
            categories = {}
            for item in menu_items.values():
                cat = item.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            st.write("**Categories:**")
            for cat, count in categories.items():
                st.write(f"• {cat}: {count} items")
                
            # Dietary tags breakdown
            all_tags = []
            for item in menu_items.values():
                all_tags.extend(item.get('tags', []))
            
            if all_tags:
                tag_counts = {}
                for tag in all_tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                st.write("**Dietary Options:**")
                for tag, count in tag_counts.items():
                    st.write(f"• {tag}: {count} items")
        else:
            st.info("No menu items found. Click 'Add Sample Data' to get started!")

# EventBot AI Chat Page - PURE GEMINI AI, NO RULES!
elif page == "EventBot AI Chat":
    st.header("🤖 EventBot AI Assistant")
    st.write("**100% Pure Gemini AI + Firebase Admin SDK** 🧠🔥 - Ask me ANYTHING!")
    
    # Load data for chatbot
    ingredients = get_ingredient_inventory()
    menu_items = get_menu_items()
    
    # Show data status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🥕 Ingredients", len(ingredients))
    with col2:
        st.metric("🍽️ Menu Items", len(menu_items))
    with col3:
        st.metric("🔥 Firebase", "✅ Admin SDK" if db else "❌ Error")
    
    # API Test Button
    if st.button("🔧 Test Gemini AI Connection"):
        test_response = call_gemini_ai_direct("Hello, are you working?", ingredients, menu_items)
        st.write("**Test Response:**")
        st.write(test_response)
    
    # Chat interface
    if "pure_ai_messages" not in st.session_state:
        st.session_state.pure_ai_messages = [
            {"role": "assistant", "content": f"""Hello! I'm EventBot, your AI restaurant assistant! 🍽️

**Current Status:**
• **{len(ingredients)} ingredients** in inventory
• **{len(menu_items)} menu items** available
• **Firebase Admin SDK** connected! 🔥
• **Gemini AI** ready to help! 🧠

I can help you with anything about your restaurant - inventory management, menu planning, event ideas, cooking suggestions, data analysis, and much more!

What would you like to know?"""}
        ]
    
    # Display chat messages
    for message in st.session_state.pure_ai_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input - DIRECT TO GEMINI, NO PROCESSING!
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to chat history
        st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Send DIRECTLY to Gemini AI with NO preprocessing
        with st.chat_message("assistant"):
            with st.spinner("🧠 Gemini AI is thinking..."):
                # DIRECT CALL - User input goes straight to Gemini!
                ai_response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.pure_ai_messages.append({"role": "assistant", "content": ai_response})
    
    # Quick buttons that send DIRECT prompts to Gemini
    st.subheader("🚀 Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔴 Expiry Check"):
            prompt = "What ingredients are expired or expiring soon?"
            st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.session_state.pure_ai_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🥗 Vegetarian Options"):
            prompt = "Show me vegetarian ingredients and menu items"
            st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.session_state.pure_ai_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("👨‍🍳 What Can I Cook?"):
            prompt = "What can I cook with my current ingredients?"
            st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.session_state.pure_ai_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # More quick buttons
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("🎉 Event Ideas"):
            prompt = "Give me creative event menu ideas"
            st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.session_state.pure_ai_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col5:
        if st.button("🌱 Vegan Magic"):
            prompt = "Show me vegan options and creative ideas"
            st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.session_state.pure_ai_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col6:
        if st.button("📊 Data Insights"):
            prompt = "Analyze my restaurant data and give insights"
            st.session_state.pure_ai_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai_direct(prompt, ingredients, menu_items)
            st.session_state.pure_ai_messages.append({"role": "assistant", "content": response})
            st.rerun()

# Ingredient Inventory Page
elif page == "Ingredient Inventory":
    st.header("📦 Ingredient Inventory Management")
    
    tab1, tab2 = st.tabs(["View Inventory", "Add Ingredient"])
    
    with tab1:
        st.subheader("Current Inventory")
        ingredients = get_ingredient_inventory()
        
        if ingredients:
            # Convert to DataFrame for better display
            df_data = []
            for name, data in ingredients.items():
                # Check if expired
                is_expired = False
                try:
                    expiry_date = datetime.strptime(data.get('Expiry', ''), '%Y-%m-%d').date()
                    is_expired = expiry_date < datetime.now().date()
                except:
                    pass
                
                df_data.append({
                    'Ingredient': name,
                    'Quantity': data.get('Quantity', ''),
                    'Expiry': data.get('Expiry', ''),
                    'Type': data.get('Type', ''),
                    'Alternatives': data.get('Alternatives', ''),
                    'Status': '🔴 EXPIRED' if is_expired else '🟢 Fresh'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Filter options
            st.subheader("🔍 Filter Inventory")
            col1, col2 = st.columns(2)
            
            with col1:
                filter_type = st.selectbox("Filter by Type:", ["All"] + list(set(item.get('Type', '') for item in ingredients.values())))
            
            with col2:
                filter_status = st.selectbox("Filter by Status:", ["All", "Fresh", "Expired"])
            
            # Apply filters
            filtered_df = df.copy()
            if filter_type != "All":
                filtered_df = filtered_df[filtered_df['Type'] == filter_type]
            
            if filter_status == "Fresh":
                filtered_df = filtered_df[filtered_df['Status'] == '🟢 Fresh']
            elif filter_status == "Expired":
                filtered_df = filtered_df[filtered_df['Status'] == '🔴 EXPIRED']
            
            if len(filtered_df) != len(df):
                st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No ingredients in inventory")
    
    with tab2:
        st.subheader("Add New Ingredient")
        
        with st.form("add_ingredient_form"):
            name = st.text_input("Ingredient Name*")
            quantity = st.text_input("Quantity (e.g., '4 kg')*")
            expiry = st.date_input("Expiry Date*")
            ingredient_type = st.selectbox("Type*", ["vegetarian", "vegan", "mixed"])
            alternatives = st.text_input("Alternatives (comma-separated)")
            
            submitted = st.form_submit_button("Add Ingredient")
            
            if submitted:
                if name and quantity and expiry:
                    expiry_str = expiry.strftime('%Y-%m-%d')
                    if add_ingredient(name, quantity, expiry_str, ingredient_type, alternatives):
                        st.success(f"✅ Added {name} to inventory!")
                        st.rerun()
                    else:
                        st.error("Failed to add ingredient")
                else:
                    st.error("Please fill in all required fields")

# Menu Management Page
elif page == "Menu Management":
    st.header("🍽️ Menu Management")
    
    tab1, tab2 = st.tabs(["View Menu", "Add Menu Item"])
    
    with tab1:
        st.subheader("Current Menu")
        menu_items = get_menu_items()
        
        if menu_items:
            # Category filter
            categories = list(set(item.get('category', '') for item in menu_items.values()))
            selected_category = st.selectbox("Filter by Category:", ["All"] + categories)
            
            # Dietary filter
            all_tags = set()
            for item in menu_items.values():
                all_tags.update(item.get('tags', []))
            
            selected_dietary = st.multiselect("Filter by Dietary Tags:", list(all_tags))
            
            # Display filtered menu items
            for item_id, item in menu_items.items():
                # Apply filters
                if selected_category != "All" and item.get('category') != selected_category:
                    continue
                
                if selected_dietary and not any(tag in item.get('tags', []) for tag in selected_dietary):
                    continue
                
                with st.expander(f"{item.get('name', 'Unnamed Item')} ({item.get('category', 'No Category')})"):
                    st.write(f"**Description:** {item.get('description', 'No description')}")
                    st.write(f"**Ingredients:** {', '.join(item.get('ingredients', []))}")
                    
                    if item.get('tags'):
                        tags_display = " ".join([f"🏷️ {tag}" for tag in item.get('tags', [])])
                        st.write(f"**Tags:** {tags_display}")
        else:
            st.info("No menu items found")
    
    with tab2:
        st.subheader("Add New Menu Item")
        
        # Get available ingredients for selection
        ingredients = get_ingredient_inventory()
        available_ingredients = list(ingredients.keys()) if ingredients else []
        
        with st.form("add_menu_item_form"):
            item_id = st.text_input("Item ID*")
            name = st.text_input("Dish Name*")
            description = st.text_area("Description*")
            category = st.selectbox("Category*", ["Starter", "Main", "Dessert", "Beverage"])
            
            selected_ingredients = st.multiselect("Ingredients*", available_ingredients)
            
            # Common dietary tags
            dietary_tags = st.multiselect("Dietary Tags", 
                ["vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free", "spicy", "halal", "kosher"])
            
            submitted = st.form_submit_button("Add Menu Item")
            
            if submitted:
                if item_id and name and description and selected_ingredients:
                    if add_menu_item(item_id, name, description, category, selected_ingredients, dietary_tags):
                        st.success(f"✅ Added {name} to menu!")
                        st.rerun()
                    else:
                        st.error("Failed to add menu item")
                else:
                    st.error("Please fill in all required fields")

# Event Planning Page
elif page == "Event Planning":
    st.header("🎉 Event Planning")
    
    st.subheader("Plan Your Event Menu")
    
    menu_items = get_menu_items()
    ingredients = get_ingredient_inventory()
    
    if not menu_items:
        st.warning("No menu items available. Please add menu items first.")
    else:
        # Event details
        col1, col2 = st.columns(2)
        
        with col1:
            event_name = st.text_input("Event Name")
            event_date = st.date_input("Event Date")
            guest_count = st.number_input("Number of Guests", min_value=1, value=50)
        
        with col2:
            dietary_requirements = st.multiselect("Dietary Requirements", 
                ["vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free", "halal", "kosher"])
            
            budget_per_person = st.number_input("Budget per Person ($)", min_value=0.0, value=25.0, step=0.50)
        
        # AI Event Planning Assistant - DIRECT GEMINI CALL
        st.subheader("🤖 Pure Gemini AI Event Planner")
        if st.button("✨ Get AI Event Plan", type="primary"):
            # Send event details DIRECTLY to Gemini
            planning_prompt = f"""Plan an event for me! Event: {event_name}, Date: {event_date}, Guests: {guest_count}, Dietary requirements: {dietary_requirements}, Budget: ${budget_per_person} per person. Create a complete event plan with menu suggestions from my available dishes."""
            
            with st.spinner("🧠 Gemini AI is planning your event..."):
                ai_response = call_gemini_ai_direct(planning_prompt, ingredients, menu_items)
            
            st.write("**✨ Your AI Event Plan:**")
            st.markdown(ai_response)
        
        st.subheader("Select Menu Items")
        
        # Filter menu items by dietary requirements
        filtered_menu = {}
        for item_id, item in menu_items.items():
            item_tags = item.get('tags', [])
            if not dietary_requirements or any(req in item_tags for req in dietary_requirements):
                filtered_menu[item_id] = item
        
        # Organize by category
        categories = {}
        for item_id, item in filtered_menu.items():
            cat = item.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((item_id, item))
        
        selected_items = []
        
        for category, items in categories.items():
            st.write(f"**{category}s:**")
            for item_id, item in items:
                if st.checkbox(f"{item.get('name')} - {item.get('description', '')[:50]}...", key=item_id):
                    selected_items.append((item_id, item))
        
        if selected_items:
            st.subheader("📋 Event Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Event:** {event_name}")
                st.write(f"**Date:** {event_date}")
                st.write(f"**Guests:** {guest_count}")
                st.write(f"**Budget:** ${budget_per_person * guest_count:.2f} total")
            
            with col2:
                if dietary_requirements:
                    st.write("**Dietary Requirements:**")
                    for req in dietary_requirements:
                        st.write(f"• {req}")
            
            st.write("**Selected Menu Items:**")
            for item_id, item in selected_items:
                st.write(f"• {item.get('name')} ({item.get('category')})")
            
            # Calculate ingredient requirements
            st.subheader("📦 Ingredient Requirements")
            required_ingredients = {}
            
            for item_id, item in selected_items:
                for ingredient in item.get('ingredients', []):
                    if ingredient in required_ingredients:
                        required_ingredients[ingredient] += 1
                    else:
                        required_ingredients[ingredient] = 1
            
            # Check availability
            st.write("**Ingredient Availability Check:**")
            missing_ingredients = []
            
            for ingredient, needed in required_ingredients.items():
                if ingredient in ingredients:
                    available_qty = ingredients[ingredient].get('Quantity', 'Unknown')
                    expiry = ingredients[ingredient].get('Expiry', 'Unknown')
                    
                    # Check if expired
                    is_expired = False
                    try:
                        expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date()
                        is_expired = expiry_date < datetime.now().date()
                    except:
                        pass
                    
                    if is_expired:
                        st.write(f"⚠️ {ingredient}: Available but EXPIRED ({expiry})")
                        missing_ingredients.append(ingredient)
                    else:
                        st.write(f"✅ {ingredient}: Available ({available_qty}, expires {expiry})")
                else:
                    st.write(f"❌ {ingredient}: Not in inventory")
                    missing_ingredients.append(ingredient)
            
            if missing_ingredients:
                st.subheader("🛒 Shopping List")
                st.write("**Items to purchase:**")
                for ingredient in missing_ingredients:
                    st.write(f"• {ingredient}")

# Footer
st.markdown("---")
st.markdown("*EventBot - 100% Pure Gemini AI + Firebase Admin SDK 🧠🔥*")
