import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Initialize Firebase Admin SDK
@st.cache_resource
def initialize_firebase():
    # Path to the Firebase service account JSON file
    service_account_path = "/mount/src/send-help/restaurant-data-backend-firebase-adminsdk.json"
    
    try:
        # Check if file exists
        if not os.path.exists(service_account_path):
            st.error(f"Service account file not found at: {service_account_path}. Please ensure the Firebase service account JSON file is correctly placed.")
            return None
        
        # Initialize Firebase only if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except ValueError as e:
        st.error(f"Failed to initialize Firebase: {str(e)}. Please check the service account JSON file.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while initializing Firebase: {str(e)}")
        return None

# Function to fetch ingredient inventory
def get_ingredient_inventory(db):
    if db is None:
        return []
    inventory_ref = db.collection("ingredient_inventory")
    docs = inventory_ref.stream()
    inventory = []
    for doc in docs:
        data = doc.to_dict()
        data["ingredient_name"] = doc.id
        inventory.append(data)
    return inventory

# Function to fetch menu items
def get_menu_items(db):
    if db is None:
        return []
    menu_ref = db.collection("menu")
    docs = menu_ref.stream()
    menu_items = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        menu_items.append(data)
    return menu_items

# Initialize Streamlit app
st.title("Restaurant Event Planning System")

# Initialize Firebase
db = initialize_firebase()

# Check if Firebase initialization failed
if db is None:
    st.error("Cannot connect to Firestore. Please check the error messages above and try again.")
    st.stop()

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Select a page:", ["Inventory", "Menu"])

# Inventory Page
if page == "Inventory":
    st.header("Ingredient Inventory")
    
    # Fetch inventory data
    inventory = get_ingredient_inventory(db)
    
    # Filter options
    type_filter = st.selectbox("Filter by Type", ["All", "vegetarian", "vegan", "mixed"])
    expiry_filter = st.date_input("Show ingredients expiring before", value=None, min_value=datetime(2025, 1, 1))
    
    # Display inventory
    st.subheader("Ingredients")
    if not inventory:
        st.write("No inventory items found or failed to connect to Firestore.")
    for item in inventory:
        if type_filter != "All" and item["Type"] != type_filter:
            continue
        if expiry_filter and item["Expiry"] and datetime.strptime(item["Expiry"], "%Y-%m-%d").date() > expiry_filter:
            continue
        st.write(f"**{item['ingredient_name']}**")
        st.write(f"Quantity: {item['Quantity']}")
        st.write(f"Expiry: {item['Expiry']}")
        st.write(f"Type: {item['Type']}")
        st.write(f"Alternatives: {item['Alternatives']}")
        st.write("---")

# Menu Page
elif page == "Menu":
    st.header("Menu Items")
    
    # Fetch menu data
    menu_items = get_menu_items(db)
    
    # Filter options
    category_filter = st.selectbox("Filter by Category", ["All", "Starter", "Main", "Dessert"])
    tag_filter = st.multiselect("Filter by Dietary Tags", ["vegetarian", "gluten-free", "vegan", "nut-free"])
    
    # Display menu items
    st.subheader("Dishes")
    if not menu_items:
        st.write("No menu items found or failed to connect to Firestore.")
    for item in menu_items:
        if category_filter != "All" and item["category"] != category_filter:
            continue
        if tag_filter and not all(tag in item["tags"] for tag in tag_filter):
            continue
        st.write(f"**{item['name']}**")
        st.write(f"Description: {item['description']}")
        st.write(f"Category: {item['category']}")
        st.write(f"Ingredients: {', '.join(item['ingredients'])}")
        st.write(f"Tags: {', '.join(item['tags'])}")
        st.write("---")
