import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import google.generativeai as genai
import traceback

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAdOsM8ZyjaclxIzy29AdPLLop-NOH4GLw"
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Failed to configure Gemini API: {str(e)}")

# Initialize Firebase Admin SDK
@st.cache_resource
def initialize_firebase():
    try:
        # Service account credentials embedded directly
        firebase_config = {
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
        cred = credentials.Certificate(firebase_config)
        
        # Initialize Firebase only if not already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except ValueError as e:
        st.error(f"Failed to initialize Firebase: {str(e)}. Please check the embedded service account credentials.")
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

# Chatbot Anna using Gemini API
def chatbot_anna(db, user_input):
    if not user_input:
        return "Please enter a question for Anna."
    try:
        # Fetch inventory and menu for context
        ingredients = get_ingredient_inventory(db)
        menu_items = get_menu_items(db)
        
        # Prepare context
        ingredient_names = [item["ingredient_name"] for item in ingredients]
        ingredient_details = "\n".join([f"- {item['ingredient_name']}: {item['Quantity']}, Expiry: {item['Expiry']}, Type: {item['Type']}" for item in ingredients])
        menu_details = "\n".join([f"- {item['name']}: {item['description']}, Category: {item['category']}, Ingredients: {', '.join(item['ingredients'])}, Tags: {', '.join(item['tags'])}" for item in menu_items])
        
        # Construct prompt
        prompt = (
            f"You are Anna, a helpful restaurant event-planning assistant. Use the following data to answer the user's question:\n"
            f"**Inventory**:\n{ingredient_details if ingredients else 'No ingredients available.'}\n"
            f"**Menu**:\n{menu_details if menu_items else 'No menu items available.'}\n"
            f"User question: {user_input}\n"
            "Provide a concise and helpful response. For recipe suggestions, use available ingredients. For menu questions, reference menu items and their tags."
        )
        
        # Debug: Show prompt
        st.write("**Debug**: Sending prompt to Gemini API...")
        # st.write(f"Prompt: {prompt[:500]}...")  # Truncated for brevity
        
        # Initialize model and generate response
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        if not response.text:
            return "Anna received an empty response from the Gemini API. Please try a different prompt."
        return response.text
    except Exception as e:
        error_msg = f"Anna encountered an error: {str(e)}\n\n**Traceback**:\n{traceback.format_exc()}"
        st.error(error_msg)
        return f"Sorry, Anna couldn't respond due to an error: {str(e)}. Please check the API key or try again later."

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
page = st.sidebar.radio("Select a page:", ["Inventory", "Menu", "Chat with Anna"])

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

# Chatbot Anna Page
elif page == "Chat with Anna":
    st.header("Chat with Anna")
    st.write("Ask Anna for recipe suggestions, menu information, or event planning tips!")
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    user_input = st.chat_input("Your question for Anna:")
    if user_input:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get Anna's response
        with st.chat_message("assistant"):
            response = chatbot_anna(db, user_input)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
