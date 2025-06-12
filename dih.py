import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from datetime import datetime

# Initialize Firebase Admin SDK
@st.cache_resource
def initialize_firebase():
    # Firebase configuration
    firebase_config = {
        "type": "service_account",
        "project_id": "restaurant-data-backend",
        "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID", "mock_key_id"),
        "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"),
        "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL", "mock@restaurant-data-backend.iam.gserviceaccount.com"),
        "client_id": os.environ.get("FIREBASE_CLIENT_ID", "mock_client_id"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL", "mock_cert_url")
    }
    
    # Initialize Firebase only if not already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Function to fetch ingredient inventory
def get_ingredient_inventory(db):
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
