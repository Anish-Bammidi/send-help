import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import requests
import os

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
    ["Dashboard", "Ingredient Inventory", "Menu Management", "Event Planning", "EventBot Chat"]
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

# EventBot Chat Page
elif page == "EventBot Chat":
    st.header("🤖 EventBot AI Assistant")
    
    # Load data for chatbot
    ingredients = get_ingredient_inventory()
    menu_items = get_menu_items()
    
    # Show data status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Ingredients Available", len(ingredients))
    with col2:
        st.metric("Menu Items Available", len(menu_items))
    
    # OpenAI API key input
    with st.sidebar:
        st.subheader("🔑 OpenAI API Key")
        api_key = st.text_input("Enter your OpenAI API key", type="password")
        st.caption("Your API key is not stored and is only used for this session")
        
        if not api_key:
            st.info("👆 Enter your OpenAI API key to enable AI chat")
            
        st.divider()
        st.subheader("🧠 AI Settings")
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        st.caption("Higher = more creative, Lower = more precise")
    
    # Function to call OpenAI API
    def call_openai_api(prompt, api_key, temperature=0.7):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"""Hello! I'm EventBot, your restaurant assistant! 🍽️

**Current Database Status:**
• **{len(ingredients)} ingredients** in inventory
• **{len(menu_items)} menu items** available

{f"I'm ready to help you with your restaurant data!" if ingredients or menu_items else "⚠️ **No data found!** Please add some ingredients and menu items first, or use the 'Add Sample Data' button on the Dashboard."}

**I can help you with:**
• Inventory management and expiry tracking
• Menu information and dietary options
• Event planning and menu suggestions
• Ingredient availability checks
• Recipe and cooking assistance

What would you like to know about your restaurant?"""}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask EventBot a question...", disabled=not api_key):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response with OpenAI
        with st.chat_message("assistant"):
            with st.spinner("EventBot is thinking..."):
                # Prepare context about restaurant data
                context = "You are EventBot, an AI assistant for a restaurant's event planning system. You have access to the following restaurant data:\n\n"
                
                # Add ingredient details
                context += f"INGREDIENT INVENTORY ({len(ingredients)} items):\n"
                for name, data in ingredients.items():
                    context += f"- {name}: {data.get('Quantity', 'Unknown')} (expires: {data.get('Expiry', 'Unknown')}, type: {data.get('Type', 'Unknown')})\n"
                
                # Add menu details
                context += f"\nMENU ITEMS ({len(menu_items)} dishes):\n"
                for item_id, item in menu_items.items():
                    context += f"- {item.get('name', 'Unnamed')}: {item.get('description', 'No description')} (Category: {item.get('category', 'Unknown')}, Ingredients: {', '.join(item.get('ingredients', []))}, Tags: {', '.join(item.get('tags', []))})\n"
                
                # Add today's date for expiry calculations
                today = datetime.now().date()
                context += f"\nToday's date is {today}.\n\n"
                
                # Add the user's question
                context += f"User question: {prompt}\n\nPlease provide a helpful, detailed response based on the restaurant data above. If the data is empty, suggest adding sample data."
                
                # Call OpenAI API
                response = call_openai_api(context, api_key, temperature)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    # API key missing message
    if not api_key:
        st.info("⚠️ Please enter your OpenAI API key in the sidebar to enable the AI chat functionality.")
    
    # Quick action buttons (only show if API key is provided)
    if api_key:
        st.subheader("🚀 Quick Questions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔴 Expired Ingredients"):
                prompt = "What ingredients are expired or expiring soon? Please check the dates."
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Prepare context
                context = "You are EventBot, an AI assistant for a restaurant. You have access to the following restaurant data:\n\n"
                context += f"INGREDIENT INVENTORY ({len(ingredients)} items):\n"
                for name, data in ingredients.items():
                    context += f"- {name}: {data.get('Quantity', 'Unknown')} (expires: {data.get('Expiry', 'Unknown')}, type: {data.get('Type', 'Unknown')})\n"
                context += f"\nToday's date is {datetime.now().date()}.\n\n"
                context += f"User question: {prompt}\n\nPlease provide a helpful response based on the restaurant data above."
                
                response = call_openai_api(context, api_key, temperature)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col2:
            if st.button("🥗 Vegetarian Menu"):
                prompt = "Show me all vegetarian menu items and ingredients I have available."
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Prepare context
                context = "You are EventBot, an AI assistant for a restaurant. You have access to the following restaurant data:\n\n"
                context += f"INGREDIENT INVENTORY ({len(ingredients)} items):\n"
                for name, data in ingredients.items():
                    context += f"- {name}: {data.get('Quantity', 'Unknown')} (expires: {data.get('Expiry', 'Unknown')}, type: {data.get('Type', 'Unknown')})\n"
                
                context += f"\nMENU ITEMS ({len(menu_items)} dishes):\n"
                for item_id, item in menu_items.items():
                    context += f"- {item.get('name', 'Unnamed')}: {item.get('description', 'No description')} (Category: {item.get('category', 'Unknown')}, Ingredients: {', '.join(item.get('ingredients', []))}, Tags: {', '.join(item.get('tags', []))})\n"
                
                context += f"\nUser question: {prompt}\n\nPlease provide a helpful response based on the restaurant data above."
                
                response = call_openai_api(context, api_key, temperature)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        with col3:
            if st.button("👨‍🍳 What Can We Make?"):
                prompt = "Based on my current inventory, what dishes can I make today? Check which menu items have all required ingredients available."
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Prepare context
                context = "You are EventBot, an AI assistant for a restaurant. You have access to the following restaurant data:\n\n"
                context += f"INGREDIENT INVENTORY ({len(ingredients)} items):\n"
                for name, data in ingredients.items():
                    context += f"- {name}: {data.get('Quantity', 'Unknown')} (expires: {data.get('Expiry', 'Unknown')}, type: {data.get('Type', 'Unknown')})\n"
                
                context += f"\nMENU ITEMS ({len(menu_items)} dishes):\n"
                for item_id, item in menu_items.items():
                    context += f"- {item.get('name', 'Unnamed')}: {item.get('description', 'No description')} (Category: {item.get('category', 'Unknown')}, Ingredients: {', '.join(item.get('ingredients', []))}, Tags: {', '.join(item.get('tags', []))})\n"
                
                context += f"\nToday's date is {datetime.now().date()}.\n\n"
                context += f"User question: {prompt}\n\nPlease provide a helpful response based on the restaurant data above. Check if all ingredients for each dish are available and not expired."
                
                response = call_openai_api(context, api_key, temperature)
                st.session_state.messages.append({"role": "assistant", "content": response})
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
st.markdown("*EventBot - AI Assistant for Restaurant Event Planning*")
