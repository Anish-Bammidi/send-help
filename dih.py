import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Initialize Firebase Admin SDK
@st.cache_resource
def initialize_firebase():
    try:
        # Default path for service account JSON file
        service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "/mount/src/send-help/restaurant-data-backend-firebase-adminsdk.json")
        
        # Try loading from service account JSON file
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
        else:
            # Fallback to environment variables
            firebase_config = {
                "type": "service_account",
                "project_id": "restaurant-data-backend",
                "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.environ.get("FIREBASE_PRIVATE_KEY"),
                "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.environ.get("FIREBASE_CLIENT_ID", "mock_client_id"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL")
            }
            if not all([firebase_config["private_key_id"], firebase_config["private_key"], firebase_config["client_email"]]):
                st.error(
                    f"Service account file not found at: {service_account_path}. "
                    "Environment variables (FIREBASE_PRIVATE_KEY_ID, FIREBASE_PRIVATE_KEY, FIREBASE_CLIENT_EMAIL) are also missing or incomplete. "
                    "Please provide a valid service account JSON file or set the environment variables."
                )
                return None
            cred = credentials.Certificate(firebase_config)
        
        # Initialize Firebase only if not already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except ValueError as e:
        st.error(f"Failed to initialize Firebase: {str(e)}. Please check the service account JSON file or environment variables.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while initializing Firebase: {str(e)}")
        return None

# Function to fetch ingredient inventory
def get_ingredient_inventory(db):
    if db is None:
        return []
    try:
        inventory_ref = db.collection("ingredient_inventory")
        docs = inventory_ref.stream()
        inventory = []
        for doc in docs:
            data = doc.to_dict()
            data["ingredient_name"] = doc.id
            inventory.append(data)
        return inventory
    except Exception as e:
        st.error(f"Error fetching inventory: {str(e)}")
        return []

# Function to add or update ingredient
def upsert_ingredient(db, ingredient_name, quantity, expiry, ingredient_type, alternatives):
    if db is None:
        return False
    try:
        inventory_ref = db.collection("ingredient_inventory").document(ingredient_name)
        inventory_ref.set({
            "Quantity": quantity,
            "Expiry": expiry,
            "Type": ingredient_type,
            "Alternatives": alternatives
        })
        return True
    except Exception as e:
        st.error(f"Error adding/updating ingredient: {str(e)}")
        return False

# Function to delete ingredient
def delete_ingredient(db, ingredient_name):
    if db is None:
        return False
    try:
        db.collection("ingredient_inventory").document(ingredient_name).delete()
        return True
    except Exception as e:
        st.error(f"Error deleting ingredient: {str(e)}")
        return False

# Function to fetch menu items
def get_menu_items(db):
    if db is None:
        return []
    try:
        menu_ref = db.collection("menu")
        docs = menu_ref.stream()
        menu_items = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            menu_items.append(data)
        return menu_items
    except Exception as e:
        st.error(f"Error fetching menu items: {str(e)}")
        return []

# Function to add or update menu item
def upsert_menu_item(db, dish_id, name, description, category, ingredients, tags):
    if db is None:
        return False
    try:
        menu_ref = db.collection("menu").document(dish_id)
        menu_ref.set({
            "name": name,
            "description": description,
            "category": category,
            "ingredients": ingredients,
            "tags": tags
        })
        return True
    except Exception as e:
        st.error(f"Error adding/updating menu item: {str(e)}")
        return False

# Function to delete menu item
def delete_menu_item(db, dish_id):
    if db is None:
        return False
    try:
        db.collection("menu").document(dish_id).delete()
        return True
    except Exception as e:
        st.error(f"Error deleting menu item: {str(e)}")
        return False

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
    
    # Add new ingredient
    st.subheader("Add/Update Ingredient")
    with st.form("ingredient_form"):
        ingredient_name = st.text_input("Ingredient Name")
        quantity = st.text_input("Quantity (e.g., 4 kg)")
        expiry = st.date_input("Expiry Date", min_value=datetime(2025, 1, 1))
        ingredient_type = st.selectbox("Type", ["vegetarian", "vegan", "mixed"])
        alternatives = st.text_input("Alternatives (comma-separated)")
        submit_button = st.form_submit_button("Add/Update Ingredient")
        
        if submit_button:
            if ingredient_name:
                expiry_str = expiry.strftime("%Y-%m-%d")
                if upsert_ingredient(db, ingredient_name, quantity, expiry_str, ingredient_type, alternatives):
                    st.success(f"Ingredient '{ingredient_name}' added/updated successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to add/update ingredient.")
            else:
                st.error("Ingredient name is required.")
    
    # Fetch and display inventory
    inventory = get_ingredient_inventory(db)
    
    # Filter options
    st.subheader("View Ingredients")
    type_filter = st.selectbox("Filter by Type", ["All", "vegetarian", "vegan", "mixed"])
    expiry_filter = st.date_input("Show ingredients expiring before", value=None, min_value=datetime(2025, 1, 1))
    
    # Display inventory
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
        if st.button(f"Delete {item['ingredient_name']}", key=f"delete_ingredient_{item['ingredient_name']}"):
            if delete_ingredient(db, item["ingredient_name"]):
                st.success(f"Ingredient '{item['ingredient_name']}' deleted successfully!")
                st.experimental_rerun()
            else:
                st.error(f"Failed to delete ingredient '{item['ingredient_name']}'.")
        st.write("---")

# Menu Page
elif page == "Menu":
    st.header("Menu Items")
    
    # Add new menu item
    st.subheader("Add/Update Menu Item")
    with st.form("menu_form"):
        dish_id = st.text_input("Dish ID (unique identifier)")
        name = st.text_input("Dish Name")
        description = st.text_area("Description")
        category = st.selectbox("Category", ["Starter", "Main", "Dessert"])
        ingredients = st.text_input("Ingredients (comma-separated)")
        tags = st.multiselect("Dietary Tags", ["vegetarian", "gluten-free", "vegan", "nut-free"])
        submit_button = st.form_submit_button("Add/Update Menu Item")
        
        if submit_button:
            if dish_id and name:
                ingredients_list = [i.strip() for i in ingredients.split(",") if i.strip()]
                if upsert_menu_item(db, dish_id, name, description, category, ingredients_list, tags):
                    st.success(f"Menu item '{name}' added/updated successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to add/update menu item.")
            else:
                st.error("Dish ID and name are required.")
    
    # Fetch and display menu items
    menu_items = get_menu_items(db)
    
    # Filter options
    st.subheader("View Dishes")
    category_filter = st.selectbox("Filter by Category", ["All", "Starter", "Main", "Dessert"])
    tag_filter = st.multiselect("Filter by Dietary Tags", ["vegetarian", "gluten-free", "vegan", "nut-free"])
    
    # Display menu items
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
        if st.button(f"Delete {item['name']}", key=f"delete_menu_{item['id']}"):
            if delete_menu_item(db, item["id"]):
                st.success(f"Menu item '{item['name']}' deleted successfully!")
                st.experimental_rerun()
            else:
                st.error(f"Failed to delete menu item '{item['name']}'.")
        st.write("---")
