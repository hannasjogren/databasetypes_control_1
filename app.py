import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
from streamlit_qrcode_scanner import qrcode_scanner
import qrcode
import io
from PIL import Image

uri = "mongodb+srv://hannasjogrendata24hel:qg3wr2kLapj2Z3Mz@databasetypes.6zjyu.mongodb.net/?retryWrites=true&w=majority&appName=databasetypes"
# Anslut till MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["northwind"]
collection = db["products_suppliers"]

# Hämta produkter som behöver beställas och ta bort dubbletter
def get_products_to_reorder():
    """Hämtar produkter som behöver beställas och deras leverantörer utan dubbletter."""
    query = {
        "$expr": {
            "$gt": ["$ReorderLevel", {"$add": ["$UnitsInStock", "$UnitsOnOrder"]}]
        }
    }
    
    # Använder aggregation för att gruppera produkterna efter namn och ta bort dubbletter
    pipeline = [
        {"$match": query},  # Filtrera produkter som behöver beställas
        {"$group": {
            "_id": "$ProductName",  # Grupp efter produktnamn
            "ProductName": {"$first": "$ProductName"},
            "CompanyName": {"$first": "$CompanyName"},
            "ContactName": {"$first": "$ContactName"},
            "Phone": {"$first": "$Phone"}
        }}
    ]
    
    return list(collection.aggregate(pipeline))

# Streamlit-app för att visa produkter som behöver beställas
st.title("📦 Beställningsbehov – Northwind")

# Hämta produkter som behöver beställas från MongoDB
products_to_reorder = get_products_to_reorder()

# Om inga produkter behöver beställas
if not products_to_reorder:
    st.success("🎉 Alla produkter är i lager!")
else:
    # Visa varningar för produkter som behöver beställas
    st.warning("⚠️ Följande produkter behöver beställas:")
    
    # Iterera och visa produktinformation för varje produkt som behöver beställas
    for product in products_to_reorder:
        st.subheader(f"📌 {product['ProductName']}")
        st.write(f"**Leverantör:** {product['CompanyName']}")
        st.write(f"**Kontaktperson:** {product['ContactName']}")
        st.write(f"📞 **Telefon:** {product['Phone']}")
        st.divider()  # Divider mellan produkterna
        
# Skapa QR-kod
def create_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    # Konvertera PIL-bilden till en bytes-ström
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

# Streamlit appen
st.title("QR-kod Generering och Skanning")
st.write("Skapa QR-kod eller skanna för att hämta produktinformation.")

# QR-kod skapare
st.header("Skapa en QR-kod")
input_data = st.text_input("Skriv ett produkt-ID:")

if input_data:
    qr_img = create_qr_code(input_data)
    st.image(qr_img, caption="QR-kod för skanning", use_column_width=True)

# QR-kod scanning
st.header("Skanna QR-kod")
qr_code = qrcode_scanner()

if qr_code:
    try:
        # Sök efter produkt-ID i MongoDB baserat på QR-koden
        product_data = collection.find_one({"ProductID": int(qr_code)})

        # Om produkten finns
        if product_data:
            st.write(f"**Produktinformation för ID: {qr_code}**")
            st.json(product_data)  # Visa produktdata i JSON-format

            # Visa datan som en DataFrame
            df = pd.DataFrame([product_data])  # Gör om till DataFrame (en rad)
            st.dataframe(df)

        else:
            st.error(f"Ingen produkt hittades för QR-kod: {qr_code}")
    
    except Exception as e:
        st.error(f"Ett fel uppstod vid hämtning av data: {str(e)}")