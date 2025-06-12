import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime, date
import pandas as pd

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyAWwy0-N_KMeXF8p5wOCew-OJz9oFQSm5A",
    "authDomain": "restaurant-data-backend.firebaseapp.com",
    "projectId": "restaurant-data-backend",
    "storageBucket": "restaurant-data-backend.firebasestorage.app",
    "messagingSenderId": "1080257817525",
    "appId": "1:1080257817525:web:0b1a9cdb5b8d5abe8d07fc",
    "measurementId": "G-2K3GHNE916"
}

# Initialize Firebase (only once)
@st.cache_resource
def init_firebase():
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize Firebase with project ID
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": firebase_config["projectId"],
            # Note: For production, use proper service account credentials
        })
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

# Initialize Firestore client
db = init_firebase()

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
    ["Dashboard", "Ingredient Inventory", "Menu Management", "Event Planning"]
)

# Helper Functions
def get_ingredient_inventory():
    """Fetch all ingredients from Firestore"""
    try:
        ingredients_ref = db.collection('ingredient_inventory')
        docs = ingredients_ref.stream()
        
        ingredients = {}
        for doc in docs:
            data = doc.to_dict()
            ingredients[doc.id] = data
        return ingredients
    except Exception as e:
        st.error(f"Error fetching ingredients: {e}")
        return {}

def get_menu_items():
    """Fetch all menu items from Firestore"""
    try:
        menu_ref = db.collection('menu')
        docs = menu_ref.stream()
        
        menu_items = {}
        for doc in docs:
            data = doc.to_dict()
            menu_items[doc.id] = data
        return menu_items
    except Exception as e:
        st.error(f"Error fetching menu items: {e}")
        return {}

def add_ingredient(name, quantity, expiry, ingredient_type, alternatives):
    """Add new ingredient to inventory"""
    try:
        doc_ref = db.collection('ingredient_inventory').document(name)
        doc_ref.set({
            'Quantity': quantity,
            'Expiry': expiry,
            'Type': ingredient_type,
            'Alternatives': alternatives
        })
        return True
    except Exception as e:
        st.error(f"Error adding ingredient: {e}")
        return False

def add_menu_item(item_id, name, description, category, ingredients, tags):
    """Add new menu item"""
    try:
        doc_ref = db.collection('menu').document(item_id)
        doc_ref.set({
            'name': name,
            'description': description,
            'category': category,
            'ingredients': ingredients,
            'tags': tags
        })
        return True
    except Exception as e:
        st.error(f"Error adding menu item: {e}")
        return False

# Dashboard Page
if page == "Dashboard":
    st.header("📊 Dashboard")
    
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
                    st.write(f"• {name}: {days} days")
        else:
            st.info("No ingredients found in inventory")
    
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
        else:
            st.info("No menu items found")

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
                df_data.append({
                    'Ingredient': name,
                    'Quantity': data.get('Quantity', ''),
                    'Expiry': data.get('Expiry', ''),
                    'Type': data.get('Type', ''),
                    'Alternatives': data.get('Alternatives', '')
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Filter options
            st.subheader("🔍 Filter Inventory")
            filter_type = st.selectbox("Filter by Type:", ["All"] + list(set(item.get('Type', '') for item in ingredients.values())))
            
            if filter_type != "All":
                filtered_df = df[df['Type'] == filter_type]
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
            
            for item_id, item in menu_items.items():
                if selected_category == "All" or item.get('category') == selected_category:
                    with st.expander(f"{item.get('name', 'Unnamed Item')} ({item.get('category', 'No Category')})"):
                        st.write(f"**Description:** {item.get('description', 'No description')}")
                        st.write(f"**Ingredients:** {', '.join(item.get('ingredients', []))}")
                        st.write(f"**Tags:** {', '.join(item.get('tags', []))}")
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
                ["vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free", "spicy"])
            
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
                ["vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free"])
        
        st.subheader("Select Menu Items")
        
        # Filter menu items by dietary requirements
        filtered_menu = {}
        for item_id, item in menu_items.items():
            item_tags = item.get('tags', [])
            if not dietary_requirements or any(req in item_tags for req in dietary_requirements):
                filtered_menu[item_id] = item
        
        selected_items = []
        for item_id, item in filtered_menu.items():
            if st.checkbox(f"{item.get('name')} ({item.get('category')})", key=item_id):
                selected_items.append((item_id, item))
        
        if selected_items:
            st.subheader("📋 Event Summary")
            st.write(f"**Event:** {event_name}")
            st.write(f"**Date:** {event_date}")
            st.write(f"**Guests:** {guest_count}")
            
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
            for ingredient, needed in required_ingredients.items():
                if ingredient in ingredients:
                    available_qty = ingredients[ingredient].get('Quantity', 'Unknown')
                    expiry = ingredients[ingredient].get('Expiry', 'Unknown')
                    st.write(f"✅ {ingredient}: Available ({available_qty}, expires {expiry})")
                else:
                    st.write(f"❌ {ingredient}: Not in inventory")

# Footer
st.markdown("---")
st.markdown("*EventBot - AI Assistant for Restaurant Event Planning*")
