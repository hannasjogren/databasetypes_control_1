import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
from streamlit_qrcode_scanner import qrcode_scanner
import qrcode
import io
import json
from PIL import Image

# MongoDB URI
uri = "mongodb+srv://hannasjogrendata24hel:qg3wr2kLapj2Z3Mz@databasetypes.6zjyu.mongodb.net/?retryWrites=true&w=majority&appName=databasetypes"

# Anslut till MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["northwind"]
collection = db["products_suppliers"]

# Hämta produkter som behöver beställas och ta bort dubbletter
def get_products_to_reorder():
    query = {
        "$expr": {
            "$gt": ["$ReorderLevel", {"$add": ["$UnitsInStock", "$UnitsOnOrder"]}]
        }
    }

    pipeline = [
        {"$match": query},  
        {"$group": {
            "_id": "$ProductName",
            "ProductName": {"$first": "$ProductName"},
            "CompanyName": {"$first": "$CompanyName"},
            "ContactName": {"$first": "$ContactName"},
            "Phone": {"$first": "$Phone"}
        }}
    ]
    
    return list(collection.aggregate(pipeline))

# Skapa QR-kod med produktdata som JSON
def create_qr_code(product):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    product_json = json.dumps(product)
    qr.add_data(product_json)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# Streamlit-app
st.title("📦 Beställningsbehov – Northwind")

# Hämta produkter som behöver beställas från MongoDB
products_to_reorder = get_products_to_reorder()

# Om inga produkter behöver beställas
if not products_to_reorder:
    st.success("🎉 Alla produkter är i lager!")
else:
    st.warning("⚠️ Följande produkter behöver beställas:")
    
    for product in products_to_reorder:
        st.subheader(f"📌 {product['ProductName']}")
        st.write(f"**Leverantör:** {product['CompanyName']}")
        st.write(f"**Kontaktperson:** {product['ContactName']}")
        st.write(f"📞 **Telefon:** {product['Phone']}")

        # Generera och visa QR-kod
        qr_img = create_qr_code(product)
        st.image(qr_img, caption=f"QR-kod för {product['ProductName']}", use_column_width=False)

        st.divider()

# QR-kod scanning
st.header("📸 Skanna en QR-kod")
qr_code = qrcode_scanner()

if qr_code:
    try:
        # Försök att tolka QR-koden som JSON
        product_data = json.loads(qr_code)

        # Visa produktinfo
        st.write(f"**Produktinformation:**")
        st.json(product_data)  

        # Visa data i tabellformat
        df = pd.DataFrame([product_data])  
        st.dataframe(df)

    except json.JSONDecodeError:
        st.error("QR-koden innehåller inte giltig produktdata.")
    except Exception as e:
        st.error(f"Ett fel uppstod: {str(e)}")