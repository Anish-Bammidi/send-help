import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import requests

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyAdOsM8ZyjaclxIzy29AdPLLop-NOH4GLw",
    "authDomain": "restaurant-data-backend.firebaseapp.com",
    "projectId": "restaurant-data-backend",
    "storageBucket": "restaurant-data-backend.firebasestorage.app",
    "messagingSenderId": "1080257817525",
    "appId": "1:1080257817525:web:0b1a9cdb5b8d5abe8d07fc",
    "measurementId": "G-2K3GHNE916"
}

# GEMINI AI API KEY (YOUR KEY!)
GEMINI_API_KEY = "AIzaSyAdOsM8ZyjaclxIzy29AdPLLop-NOH4GLw"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# Firebase REST API base URL
FIREBASE_URL = f"https://firestore.googleapis.com/v1/projects/{firebase_config['projectId']}/databases/(default)/documents"

# Helper Functions for Firebase REST API
def get_collection(collection_name):
    """Fetch all documents from a collection using Firebase REST API"""
    try:
        response = requests.get(f"{FIREBASE_URL}/{collection_name}")
        if response.status_code == 200:
            data = response.json()
            documents = {}
            
            if 'documents' in data:
                for doc in data['documents']:
                    doc_id = doc['name'].split('/')[-1]
                    doc_data = {}
                    
                    if 'fields' in doc:
                        for field_name, field_value in doc['fields'].items():
                            # Extract the value based on its type
                            value_type = list(field_value.keys())[0]
                            
                            if value_type == 'stringValue':
                                doc_data[field_name] = field_value['stringValue']
                            elif value_type == 'arrayValue':
                                if 'values' in field_value['arrayValue']:
                                    doc_data[field_name] = [v['stringValue'] for v in field_value['arrayValue']['values']]
                                else:
                                    doc_data[field_name] = []
                            elif value_type == 'integerValue':
                                doc_data[field_name] = int(field_value['integerValue'])
                            elif value_type == 'doubleValue':
                                doc_data[field_name] = float(field_value['doubleValue'])
                            elif value_type == 'booleanValue':
                                doc_data[field_name] = field_value['booleanValue']
                    
                    documents[doc_id] = doc_data
            
            return documents
        else:
            return {}
    except Exception as e:
        st.error(f"Firebase Error: {e}")
        return {}

def add_document(collection_name, doc_id, data):
    """Add a document to a collection using Firebase REST API"""
    try:
        # Convert Python data to Firestore format
        firestore_data = {"fields": {}}
        
        for key, value in data.items():
            if isinstance(value, str):
                firestore_data["fields"][key] = {"stringValue": value}
            elif isinstance(value, list):
                firestore_data["fields"][key] = {
                    "arrayValue": {
                        "values": [{"stringValue": item} for item in value]
                    }
                }
            elif isinstance(value, int):
                firestore_data["fields"][key] = {"integerValue": str(value)}
            elif isinstance(value, float):
                firestore_data["fields"][key] = {"doubleValue": value}
            elif isinstance(value, bool):
                firestore_data["fields"][key] = {"booleanValue": value}
        
        # Use PUT to set document with custom ID
        response = requests.put(
            f"{FIREBASE_URL}/{collection_name}/{doc_id}",
            json=firestore_data
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error adding document: {e}")
        return False

def call_gemini_ai(user_message, ingredients_data, menu_data):
    """Call Google Gemini AI API with restaurant context"""
    try:
        # Prepare context about the restaurant data
        context = f"""You are EventBot, an intelligent AI assistant for a restaurant's event-planning system. You have access to real-time restaurant data and should provide helpful, conversational responses.

CURRENT RESTAURANT DATA:

INGREDIENT INVENTORY ({len(ingredients_data)} items):
"""
        
        # Add ingredient details
        for name, data in ingredients_data.items():
            context += f"- {name}: {data.get('Quantity', 'Unknown')} (expires: {data.get('Expiry', 'Unknown')}, type: {data.get('Type', 'Unknown')})\n"
        
        context += f"\nMENU ITEMS ({len(menu_data)} dishes):\n"
        
        # Add menu details
        for item_id, item in menu_data.items():
            context += f"- {item.get('name', 'Unnamed')}: {item.get('description', 'No description')} (Category: {item.get('category', 'Unknown')}, Ingredients: {', '.join(item.get('ingredients', []))}, Tags: {', '.join(item.get('tags', []))})\n"
        
        context += f"""

Today's date is {datetime.now().date()}.

INSTRUCTIONS:
- Be conversational, helpful, and engaging
- Answer questions about inventory, menu items, event planning, and cooking suggestions
- Use the actual data provided above in your responses
- Be specific and reference real ingredients/dishes when relevant
- If asked about expiry dates, check the dates against today's date
- For event planning, suggest appropriate menu items from the available dishes
- If asked what can be made, check which menu items have all required ingredients available
- Be creative and provide detailed suggestions
- Use emojis to make responses more engaging

USER QUESTION: {user_message}

Please provide a helpful, detailed, and conversational response based on the restaurant data above."""

        # Prepare the API request for Gemini
        payload = {
            "contents": [{
                "parts": [{
                    "text": context
                }]
            }],
            "generationConfig": {
                "temperature": 0.8,
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
            st.error(f"Gemini API Error: {response.status_code} - {response.text}")
            return f"I'm experiencing technical difficulties with my AI brain 🧠. Error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "I'm taking longer than usual to think! ⏰ Please try your question again."
    except requests.exceptions.RequestException as e:
        return f"I'm having trouble connecting to my AI service 🌐. Please check your internet connection and try again."
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return f"I encountered an unexpected error 😅: {str(e)}. Please try again!"

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
            for name, data in sample_ingredients.items():
                add_ingredient(name, data['Quantity'], data['Expiry'], data['Type'], data['Alternatives'])
            
            # Add sample menu items
            for item_id, data in sample_menu.items():
                add_menu_item(item_id, data['name'], data['description'], data['category'], data['ingredients'], data['tags'])
            
            st.success("✅ Sample data added! Refresh the page to see the data.")
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

# EventBot AI Chat Page
elif page == "EventBot AI Chat":
    st.header("🤖 EventBot AI Assistant")
    st.write("**Powered by Google Gemini AI** 🧠✨ - Ask me anything about your restaurant!")
    
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
        st.metric("🤖 Gemini AI", "✅ Connected")
    
    # Chat interface
    if "gemini_messages" not in st.session_state:
        st.session_state.gemini_messages = [
            {"role": "assistant", "content": f"""Hey there! 👋 I'm EventBot, your AI-powered restaurant assistant running on Google Gemini! 🤖✨

**I'm connected to your live restaurant data:**
• **{len(ingredients)} ingredients** in inventory 📦
• **{len(menu_items)} menu items** available 🍽️

**I can help you with literally ANYTHING about your restaurant:**
• 🔍 Smart inventory analysis and expiry tracking
• 🥗 Menu recommendations and dietary suggestions  
• 🎉 Creative event planning and menu curation
• 👨‍🍳 Recipe ideas based on what you have
• 📊 Data insights and restaurant analytics
• 💡 Creative cooking suggestions and alternatives

**Try asking me stuff like:**
• "What's about to expire and what should I do with it?"
• "Create a romantic dinner menu for 2 people"
• "I have tomatoes and cheese, what can I make?"
• "Plan a vegan party menu for 30 guests"
• "Give me insights about my restaurant data"
• "What's the most popular ingredient I have?"

I'm powered by Google Gemini, so I can understand context, be creative, and give you detailed, helpful responses! What would you like to know? 🚀"""}
        ]
    
    # Display chat messages
    for message in st.session_state.gemini_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask EventBot anything about your restaurant..."):
        # Add user message to chat history
        st.session_state.gemini_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response with Gemini
        with st.chat_message("assistant"):
            with st.spinner("🧠 Gemini AI is thinking..."):
                ai_response = call_gemini_ai(prompt, ingredients, menu_items)
            st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.gemini_messages.append({"role": "assistant", "content": ai_response})
    
    # Quick action buttons
    st.subheader("🚀 Quick AI Questions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔴 Expiry Alert"):
            prompt = "What ingredients are expired or expiring soon? Give me a detailed analysis and suggestions for what to do with them."
            st.session_state.gemini_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai(prompt, ingredients, menu_items)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🥗 Veggie Power"):
            prompt = "Show me all my vegetarian options - both ingredients and menu items. Give me creative suggestions for vegetarian dishes I can make!"
            st.session_state.gemini_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai(prompt, ingredients, menu_items)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("👨‍🍳 Chef Mode"):
            prompt = "I want to cook something amazing! Based on my current inventory, what dishes can I make today? Be creative and give me detailed cooking suggestions!"
            st.session_state.gemini_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai(prompt, ingredients, menu_items)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # Additional quick buttons
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("🎉 Party Planner"):
            prompt = "I need to plan an awesome event! Help me create a balanced, impressive menu using my available dishes. Be creative and suggest themes!"
            st.session_state.gemini_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai(prompt, ingredients, menu_items)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col5:
        if st.button("🌱 Vegan Vibes"):
            prompt = "Show me all my vegan options and give me creative vegan menu ideas! I want to impress vegan customers."
            st.session_state.gemini_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai(prompt, ingredients, menu_items)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col6:
        if st.button("📊 Data Genius"):
            prompt = "Analyze my restaurant data like a pro! Give me insights, trends, recommendations, and suggestions for improvement."
            st.session_state.gemini_messages.append({"role": "user", "content": prompt})
            response = call_gemini_ai(prompt, ingredients, menu_items)
            st.session_state.gemini_messages.append({"role": "assistant", "content": response})
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
        
        # AI Event Planning Assistant
        st.subheader("🤖 Gemini AI Event Planning Assistant")
        if st.button("✨ Get AI Event Planning Magic", type="primary"):
            planning_prompt = f"""I need your creative help planning an amazing event! Here are the details:

Event Details:
- Event Name: {event_name}
- Date: {event_date}
- Number of Guests: {guest_count}
- Dietary Requirements: {', '.join(dietary_requirements) if dietary_requirements else 'None specified'}
- Budget per Person: ${budget_per_person}

Please be my creative event planning genius! I want you to:
1. Suggest an amazing, balanced menu from my available dishes
2. Check ingredient availability and suggest alternatives if needed
3. Give me creative presentation ideas and themes
4. Provide a complete event plan with recommendations
5. Calculate if I have enough ingredients for all guests
6. Suggest any additional items I might need

Make this event unforgettable! Be creative and detailed in your suggestions."""
            
            with st.spinner("🧠 Gemini AI is creating your magical event plan..."):
                ai_response = call_gemini_ai(planning_prompt, ingredients, menu_items)
            
            st.write("**✨ Your AI-Generated Event Plan:**")
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
st.markdown("*EventBot - AI Assistant for Restaurant Event Planning | Powered by Google Gemini AI 🧠✨*")
