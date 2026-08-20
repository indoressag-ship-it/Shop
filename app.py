import os
import sqlite3
import io
from datetime import datetime
import streamlit as st

# ReportLab Libraries for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Page Configuration
st.set_page_config(page_title="Smart Shop Manager", page_icon="🏬", layout="wide")


# ==========================================
# 📄 PROFESSIONAL PDF GENERATOR FUNCTION
# ==========================================
def generate_pdf_bytes(store_info, customer_info, items, billing_summary):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle('StoreTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor("#1E3A8A"))
    style_subtitle = ParagraphStyle('StoreSub', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor("#4B5563"))
    style_inv_title = ParagraphStyle('InvTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=22, leading=26, alignment=2, textColor=colors.HexColor("#1E3A8A"))
    style_inv_meta = ParagraphStyle('InvMeta', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13, alignment=2, textColor=colors.HexColor("#374151"))
    style_box_label = ParagraphStyle('BoxLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=12, textColor=colors.HexColor("#1F2937"))
    style_box_val = ParagraphStyle('BoxVal', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=12, textColor=colors.HexColor("#374151"))

    pincode = store_info.get('pincode', '')
    addr_line = store_info.get('address', 'Main Market')
    if pincode:
        addr_line += f" - {pincode}"

    header_data = [
        [
            Paragraph(f"<b>{store_info.get('name', 'My Shop').upper()}</b>", style_title),
            Paragraph("<b>TAX INVOICE</b>", style_inv_title)
        ],
        [
            Paragraph(f"{addr_line}<br/><b>Phone:</b> {store_info.get('phone', 'N/A')}<br/><b>GSTIN:</b> {store_info.get('gstin', 'N/A')}", style_subtitle),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %b, %Y')}<br/><b>Time:</b> {datetime.now().strftime('%I:%M %p')}", style_inv_meta)
        ]
    ]
    header_table = Table(header_data, colWidths=[320, 220])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceBefore=2, spaceAfter=10))

    udhaar_color = "#DC2626" if billing_summary['udhaar'] > 0 else "#16A34A"
    cust_data = [
        [
            Paragraph("<b>Billed To (Customer Details):</b>", style_box_label),
            Paragraph("<b>Payment Summary:</b>", style_box_label)
        ],
        [
            Paragraph(f"Name: <b>{customer_info.get('name')}</b><br/>Mobile: <b>{customer_info.get('phone', 'N/A')}</b>", style_box_val),
            Paragraph(f"Mode: <b>{billing_summary['mode']}</b><br/>Status: <font color='{udhaar_color}'><b>₹{billing_summary['udhaar']:,.2f} Udhaar Baaki</b></font>", style_box_val)
        ]
    ]
    cust_table = Table(cust_data, colWidths=[320, 220])
    cust_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(cust_table)
    story.append(Spacer(1, 15))

    table_data = [["#", "Item Description", "Price (₹)"]]
    for idx, item in enumerate(items, start=1):
        table_data.append([str(idx), item['name'], f"₹{item['price']:,.2f}"])

    table_data.append(["", "Grand Total:", f"₹{billing_summary['total']:,.2f}"])
    table_data.append(["", f"Paid ({billing_summary['mode']}):", f"₹{billing_summary['paid']:,.2f}"])
    table_data.append(["", "Balance / Udhaar:", f"₹{billing_summary['udhaar']:,.2f}"])

    item_table = Table(table_data, colWidths=[35, 365, 140])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-4), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 7),
        ('FONTNAME', (1,-3), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (1,-3), (-1,-1), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (2,-1), (2,-1), colors.HexColor("#DC2626")),
    ]))
    story.append(item_table)

    story.append(Spacer(1, 25))
    story.append(Paragraph("<b>Thank you for your business! Please visit again.</b>", ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, alignment=1, textColor=colors.HexColor("#64748B"))))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 🗄️ DATABASE MANAGEMENT
# ==========================================
class Database:
    def __init__(self, db_name="shop_dashboard_khata.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                balance REAL DEFAULT 0.0
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                phone TEXT,
                total_amount REAL,
                paid_amount REAL,
                udhaar_amount REAL,
                payment_mode TEXT,
                date DATE DEFAULT CURRENT_DATE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS store_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                address TEXT,
                pincode TEXT,
                phone TEXT,
                gstin TEXT,
                pin_code TEXT DEFAULT '1234'
            )
        ''')

        try:
            self.cursor.execute("ALTER TABLE store_info ADD COLUMN pin_code TEXT DEFAULT '1234'")
        except sqlite3.OperationalError:
            pass

        self.cursor.execute("SELECT COUNT(*) FROM store_info")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO store_info (id, name, address, pincode, phone, gstin, pin_code)
                VALUES (1, 'Apni Dukaan', 'Main Market, City', '110001', '9876543210', 'N/A', '1234')
            ''')

        self.conn.commit()

    def get_store_info(self):
        self.cursor.execute("SELECT name, address, pincode, phone, gstin, pin_code FROM store_info WHERE id = 1")
        row = self.cursor.fetchone()
        if row:
            return {
                "name": row[0],
                "address": row[1],
                "pincode": row[2],
                "phone": row[3],
                "gstin": row[4],
                "pin": row[5] if len(row) > 5 and row[5] else "1234"
            }
        return {"name": "Apni Dukaan", "address": "Main Market", "pincode": "", "phone": "", "gstin": "N/A", "pin": "1234"}

    def update_store_info(self, name, address, pincode, phone, gstin):
        self.cursor.execute('''
            UPDATE store_info 
            SET name = ?, address = ?, pincode = ?, phone = ?, gstin = ?
            WHERE id = 1
        ''', (name, address, pincode, phone, gstin))
        self.conn.commit()

    def update_pin(self, new_pin):
        self.cursor.execute("UPDATE store_info SET pin_code = ? WHERE id = 1", (new_pin,))
        self.conn.commit()


# App State Setup
db = Database()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "cart" not in st.session_state:
    st.session_state.cart = []


# ==========================================
# 🔒 PIN LOCK SYSTEM
# ==========================================
def pin_lock_screen():
    st.title("🔒 Security Lock")
    st.write("App kholne ke liye 4-Digit Security PIN darj karein:")
    
    store_data = db.get_store_info()
    correct_pin = store_data.get("pin", "1234")

    entered_pin = st.text_input("Security PIN", type="password", key="login_pin_input")
    
    if st.button("🔓 Unlock App", type="primary"):
        if entered_pin.strip() == correct_pin:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Galat PIN! Dobara koshish karein. Default PIN: 1234")


if not st.session_state.authenticated:
    pin_lock_screen()
    st.stop()


# ==========================================
# 📱 MAIN APPLICATION LAYOUT
# ==========================================
st.sidebar.title("🏬 Shop Manager")

menu = st.sidebar.radio(
    "Navigation", 
    ["📊 1. Dashboard", "🧾 2. New Bill", "💳 3. Khata Book", "⚙️ 4. Store & PIN Settings"]
)

if st.sidebar.button("🔒 Lock App"):
    st.session_state.authenticated = False
    st.rerun()

# ==========================================
# 📊 1. DASHBOARD VIEW
# ==========================================
if menu == "📊 1. Dashboard":
    st.title("Business Summary & Reports 📊")

    db.cursor.execute("SELECT SUM(total_amount), SUM(paid_amount) FROM sales")
    sales_data = db.cursor.fetchone()
    total_sales = sales_data[0] if sales_data[0] else 0.0
    total_rec = sales_data[1] if sales_data[1] else 0.0

    db.cursor.execute("SELECT SUM(balance) FROM customers")
    khata_data = db.cursor.fetchone()
    total_udhaar = khata_data[0] if khata_data[0] else 0.0

    db.cursor.execute("SELECT SUM(total_amount) FROM sales WHERE date = CURRENT_DATE")
    today_data = db.cursor.fetchone()
    today_sales = today_data[0] if today_data[0] else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{total_sales:,.2f}")
    c2.metric("Received Cash", f"₹{total_rec:,.2f}")
    c3.metric("Market Udhaar", f"₹{total_udhaar:,.2f}")
    c4.metric("Today's Sales", f"₹{today_sales:,.2f}")

    st.subheader("Recent Sales Transactions 📜")
    db.cursor.execute("SELECT id, customer_name, phone, total_amount, paid_amount, payment_mode, date FROM sales ORDER BY id DESC LIMIT 15")
    rows = db.cursor.fetchall()

    if rows:
        formatted_rows = [
            {
                "Bill ID": r[0],
                "Customer Name": r[1],
                "Mobile": r[2],
                "Total (₹)": f"₹{r[3]:,.2f}",
                "Paid (₹)": f"₹{r[4]:,.2f}",
                "Mode": r[5],
                "Date": r[6]
            }
            for r in rows
        ]
        st.dataframe(formatted_rows, use_container_width=True)
    else:
        st.info("Koi Transaction History Nahi Hai.")

# ==========================================
# 🧾 2. NEW BILLING SECTION
# ==========================================
elif menu == "🧾 2. New Bill":
    st.title("New Billing Section 🧾")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Customer Details")
        cust_name = st.text_input("Customer Name")
        cust_phone = st.text_input("Mobile Number")

        st.subheader("Add Item To Bill")
        item_name = st.text_input("Item / Product Name")
        item_price = st.number_input("Price (₹)", min_value=0.0, step=1.0)

        if st.button("➕ Add Item To Bill"):
            if not item_name or item_price <= 0:
                st.error("Sahi Item Name aur Price daalein.")
            else:
                st.session_state.cart.append({"name": item_name, "price": item_price})
                st.success(f"Added '{item_name}' to bill.")

        st.subheader("Payment Settlement")
        pay_mode = st.selectbox("Payment Mode", ["Cash", "UPI / Online", "Udhaar / Khata", "Partial Udhaar"])
        
        grand_total = sum(item['price'] for item in st.session_state.cart)
        paid_amount = st.number_input("Paid Amount (₹)", min_value=0.0, value=float(grand_total))

        if st.button("🖨️ Process & Generate Bill", type="primary"):
            if not st.session_state.cart:
                st.error("Pehle items add karein!")
            elif not cust_name or not cust_phone:
                st.error("Customer ka Name aur Phone zaroori hai.")
            else:
                if pay_mode == "Udhaar / Khata":
                    paid_amount = 0.0

                udhaar = max(0.0, grand_total - paid_amount)

                if udhaar > 0:
                    db.cursor.execute("SELECT balance FROM customers WHERE phone = ?", (cust_phone,))
                    if db.cursor.fetchone():
                        db.cursor.execute("UPDATE customers SET balance = balance + ?, name = ? WHERE phone = ?", (udhaar, cust_name, cust_phone))
                    else:
                        db.cursor.execute("INSERT INTO customers (name, phone, balance) VALUES (?, ?, ?)", (cust_name, cust_phone, udhaar))
                else:
                    db.cursor.execute("SELECT balance FROM customers WHERE phone = ?", (cust_phone,))
                    if not db.cursor.fetchone():
                        db.cursor.execute("INSERT INTO customers (name, phone, balance) VALUES (?, ?, 0.0)", (cust_name, cust_phone))

                db.cursor.execute('''
                    INSERT INTO sales (customer_name, phone, total_amount, paid_amount, udhaar_amount, payment_mode)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (cust_name, cust_phone, grand_total, paid_amount, udhaar, pay_mode))
                db.conn.commit()

                store_info = db.get_store_info()
                customer_info = {"name": cust_name, "phone": cust_phone}
                billing_summary = {"total": grand_total, "paid": paid_amount, "udhaar": udhaar, "mode": pay_mode}

                pdf_bytes = generate_pdf_bytes(store_info, customer_info, st.session_state.cart, billing_summary)

                st.success("🎉 Bill Process Ho Gaya!")
                st.download_button(
                    label="📄 Download PDF Receipt",
                    data=pdf_bytes,
                    file_name=f"{cust_name.replace(' ', '_')}_{cust_phone}.pdf",
                    mime="application/pdf"
                )
                st.session_state.cart = []

    with col_right:
        st.subheader("Current Invoice Preview 📋")
        if st.session_state.cart:
            st.dataframe(st.session_state.cart, use_container_width=True)
            st.markdown(f"### **GRAND TOTAL: ₹{grand_total:,.2f}**")
            if st.button("🗑️ Clear Cart"):
                st.session_state.cart = []
                st.rerun()
        else:
            st.info("Cart abhi khali hai.")

# ==========================================
# 💳 3. KHATA BOOK VIEW
# ==========================================
elif menu == "💳 3. Khata Book":
    st.title("Customer Khata Book & Udhaar Management 💳")

    db.cursor.execute("SELECT id, name, phone, balance FROM customers WHERE balance > 0")
    pending = db.cursor.fetchall()

    st.subheader("Clear Full Udhaar")
    if pending:
        options = {f"{r[1]} ({r[2]}) - Udhaar: ₹{r[3]:,.2f}": (r[2], r[3]) for r in pending}
        selected_cust = st.selectbox("Select Customer for Full Payment", list(options.keys()))

        if st.button("✅ Full Payment Receive"):
            phone, _ = options[selected_cust]
            db.cursor.execute("UPDATE customers SET balance = 0.0 WHERE phone = ?", (phone,))
            db.conn.commit()
            st.success("Full Payment Received!")
            st.rerun()
    else:
        st.info("Koi Udhaar Baaki Nahi Hai 🎉")

    st.divider()

    st.subheader("Partial Payment (Jama Karein)")
    if pending:
        options_part = {f"{r[1]} ({r[2]}) - Udhaar: ₹{r[3]:,.2f}": (r[2], r[3]) for r in pending}
        selected_part = st.selectbox("Select Customer for Part Payment", list(options_part.keys()))
        part_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)

        if st.button("💵 Receive Part Payment"):
            phone, current_bal = options_part[selected_part]
            if part_amount <= 0 or part_amount > current_bal:
                st.error("Sahi amount darj karein.")
            else:
                new_bal = current_bal - part_amount
                db.cursor.execute("UPDATE customers SET balance = ? WHERE phone = ?", (new_bal, phone))
                db.conn.commit()
                st.success(f"₹{part_amount:,.2f} Jama ho gaya. Naya balance: ₹{new_bal:,.2f}")
                st.rerun()

    st.divider()

    st.subheader("All Customer Khata Records")
    db.cursor.execute("SELECT name, phone, balance FROM customers ORDER BY balance DESC")
    all_cust = db.cursor.fetchall()
    if all_cust:
        khata_table = [
            {"Name": c[0], "Phone": c[1], "Status / Balance": f"₹{c[2]:,.2f} Udhaar" if c[2] > 0 else "Clear"}
            for c in all_cust
        ]
        st.dataframe(khata_table, use_container_width=True)

# ==========================================
# ⚙️ 4. STORE & PIN CHANGE SETTINGS
# ==========================================
elif menu == "⚙️ 4. Store & PIN Settings":
    st.title("Dukaan & PIN Security Settings ⚙️")

    tab_store, tab_pin = st.tabs(["🏬 Dukaan Details", "🔑 Change Security PIN"])

    store_data = db.get_store_info()

    with tab_store:
        s_name = st.text_input("Dukaan Ka Naam", value=store_data.get("name", ""))
        s_addr = st.text_input("Address (Pata)", value=store_data.get("address", ""))
        s_pin = st.text_input("PIN Code", value=store_data.get("pincode", ""))
        s_phone = st.text_input("Contact Number", value=store_data.get("phone", ""))
        s_gst = st.text_input("GSTIN (Optional)", value=store_data.get("gstin", ""))

        if st.button("💾 Save Dukaan Details"):
            if not s_name or not s_phone:
                st.error("Dukaan ka Naam aur Phone Number zaroori hai!")
            else:
                db.update_store_info(s_name, s_addr, s_pin, s_phone, s_gst if s_gst else "N/A")
                st.success("Dukaan ki details update ho gayi hain 🎉")

    with tab_pin:
        old_pin = st.text_input("Purana PIN (Old PIN)", type="password")
        new_pin = st.text_input("Naya PIN (New PIN)", type="password")
        confirm_pin = st.text_input("Confirm Naya PIN", type="password")

        if st.button("🔑 Update Security PIN"):
            current_saved_pin = db.get_store_info().get('pin', '1234')

            if old_pin != current_saved_pin:
                st.error("❌ Purana PIN sahi nahi hai!")
            elif len(new_pin) < 4:
                st.error("⚠️ Naya PIN kam se kam 4 digits ka hona chahiye.")
            elif new_pin != confirm_pin:
                st.error("❌ New PIN aur Confirm PIN match nahi ho rahe hain.")
            else:
                db.update_pin(new_pin)
                st.success("Security PIN kamyabi se badal gaya hai! 🔑")
