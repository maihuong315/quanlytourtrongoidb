import pandas as pd
import streamlit as st
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from urllib.parse import quote

# ============================================================
# TOURMATE - SMART TOUR MANAGEMENT SYSTEM
# ============================================================

st.set_page_config(
    page_title="TourMate | Quản Lý Tour Trọn Gói",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 1. DATABASE - GIỮ NGUYÊN THÔNG TIN MYSQL
# ============================================================

DB = {
    "user": "avnadmin",
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "database": "defaultdb"
}

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB["user"],
    password=DB["password"],
    host=DB["host"],
    port=DB["port"],
    database=DB["database"],
)

@st.cache_resource
def get_db_engine():
    # Aiven MySQL can use TLS. PyMySQL accepts an SSL dictionary here.
    # We keep the database credentials unchanged.
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            "connect_timeout": 20,
            "read_timeout": 30,
            "write_timeout": 30,
            "ssl": {"check_hostname": False},
        },
    )

# ============================================================
# 2. CSS
# ============================================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f7fbff 0%, #ffffff 42%);
    }

    .main-title {
        font-size: 42px;
        font-weight: 900;
        text-align: center;
        margin: 10px 0 4px 0;
        letter-spacing: -1px;
    }

    .sub-title {
        text-align: center;
        color: #607080;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .hero {
        padding: 28px;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f766e, #0284c7);
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 12px 35px rgba(2,132,199,.18);
    }

    .hero h1 {
        margin: 0;
        font-size: 38px;
    }

    .hero p {
        margin: 8px 0 0 0;
        font-size: 17px;
        opacity: .94;
    }

    .section-title {
        font-size: 27px;
        font-weight: 800;
        margin: 20px 0 15px 0;
    }

    .tour-card {
        padding: 0 0 15px 0;
        border: 1px solid #e5eaf0;
        border-radius: 18px;
        overflow: hidden;
        background: white;
        box-shadow: 0 6px 20px rgba(15,23,42,.06);
        margin-bottom: 20px;
    }

    .tour-card-body {
        padding: 14px 16px 4px 16px;
    }

    .tour-name {
        font-size: 20px;
        font-weight: 800;
        margin: 5px 0;
    }

    .price {
        font-size: 22px;
        font-weight: 900;
        color: #0f766e;
    }

    .muted {
        color: #64748b;
    }

    .stat-card {
        padding: 18px;
        border-radius: 16px;
        background: white;
        border: 1px solid #e7edf3;
        box-shadow: 0 5px 18px rgba(15,23,42,.05);
    }

    .destination-card {
        padding: 18px;
        border-radius: 18px;
        background: white;
        border: 1px solid #e5eaf0;
        box-shadow: 0 6px 20px rgba(15,23,42,.05);
        min-height: 150px;
    }

    .chat-note {
        padding: 10px 12px;
        border-radius: 12px;
        background: #eff6ff;
        color: #1e3a8a;
        font-size: 13px;
        margin-bottom: 10px;
    }

    .footer {
        text-align: center;
        color: #64748b;
        padding: 25px 0 10px 0;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e7edf3;
        padding: 12px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(15,23,42,.04);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. DATABASE HELPERS
# ============================================================

def test_database_connection():
    try:
        with get_db_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Kết nối MySQL thành công."
    except Exception as e:
        return False, str(e)

def read_query(sql, params=None):
    try:
        with get_db_engine().connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except Exception as e:
        st.error("❌ Lỗi đọc dữ liệu.")
        st.code(str(e))
        return pd.DataFrame()

def execute_query(sql, params=None):
    try:
        with get_db_engine().begin() as conn:
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        st.error("❌ Lỗi lưu dữ liệu.")
        st.code(str(e))
        return False

def init_db():
    create_tours = """
    CREATE TABLE IF NOT EXISTS tours (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tour_name VARCHAR(200) NOT NULL,
        destination VARCHAR(200) NOT NULL,
        departure_date DATE NOT NULL,
        return_date DATE NOT NULL,
        duration INT NOT NULL,
        price DECIMAL(12,2) NOT NULL,
        max_people INT NOT NULL,
        transport VARCHAR(100),
        hotel VARCHAR(200),
        meals VARCHAR(200),
        tour_guide VARCHAR(150),
        description TEXT,
        image_url TEXT,
        created_at DATETIME NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_customers = """
    CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(150) NOT NULL,
        phone VARCHAR(30) NOT NULL,
        email VARCHAR(150),
        address VARCHAR(255),
        created_at DATETIME NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    create_bookings = """
    CREATE TABLE IF NOT EXISTS bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        created_at DATETIME NOT NULL,
        customer_id INT NOT NULL,
        tour_id INT NOT NULL,
        quantity INT NOT NULL,
        total_price DECIMAL(12,2) NOT NULL,
        payment_status VARCHAR(50) NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id),
        FOREIGN KEY (tour_id) REFERENCES tours(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    with get_db_engine().begin() as conn:
        conn.exec_driver_sql(create_tours)
        conn.exec_driver_sql(create_customers)
        conn.exec_driver_sql(create_bookings)

def ensure_image_column():
    with get_db_engine().begin() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'tours'
              AND COLUMN_NAME = 'image_url'
        """))
        if result.scalar() == 0:
            conn.exec_driver_sql("ALTER TABLE tours ADD COLUMN image_url TEXT")

try:
    db_connected, db_message = test_database_connection()
except Exception as e:
    db_connected, db_message = False, str(e)

if not db_connected:
    st.error("🔴 Không thể kết nối MySQL.")
    st.warning(
        "Nếu em đang chạy trên Streamlit Cloud, hãy kiểm tra lại Host/Port/User/Password "
        "trong Aiven > Overview > Connection information. Aiven MySQL hỗ trợ kết nối "
        "qua PyMySQL và có thể yêu cầu TLS."
    )
    st.code(db_message)
    st.info(
        "Nếu lỗi có chữ 'Access denied' → thông tin đăng nhập/password không đúng. "
        "Nếu có 'Can't connect'/'timed out' → host/port hoặc network. "
        "Nếu có 'SSL'/'TLS' → cần cấu hình chứng chỉ/SSL của Aiven."
    )
    st.stop()

try:
    init_db()
    ensure_image_column()
except Exception as e:
    st.error("❌ Không thể khởi tạo Database.")
    st.code(str(e))
    st.stop()

# ============================================================
# 4. COMMON DATA
# ============================================================

DEFAULT_IMAGES = {
    "Vũng Tàu": "https://images.unsplash.com/photo-1565976469782-7c92e2b6d2f6?auto=format&fit=crop&w=1200&q=85",
    "Đà Lạt": "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=85",
    "Phú Quốc": "https://images.unsplash.com/photo-1518509562904-e7ef99cdcc86?auto=format&fit=crop&w=1200&q=85",
    "Đà Nẵng": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=85",
    "Nha Trang": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=1200&q=85",
    "Hội An": "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=85",
}

DESTINATION_INFO = {
    "Vũng Tàu": ("🌊", "Biển, nghỉ dưỡng cuối tuần và tham quan thành phố biển."),
    "Đà Lạt": ("🌲", "Khí hậu mát mẻ, thiên nhiên, cà phê và trải nghiệm check-in."),
    "Phú Quốc": ("🏝️", "Biển đảo, nghỉ dưỡng, hoàng hôn và các khu vui chơi."),
    "Đà Nẵng": ("🌉", "Biển, ẩm thực, Bà Nà Hills và hành trình miền Trung."),
    "Nha Trang": ("🐚", "Biển xanh, đảo và các hoạt động nghỉ dưỡng."),
    "Hội An": ("🏮", "Phố cổ, văn hóa, ẩm thực và trải nghiệm địa phương."),
}

def safe_image(url, fallback=None):
    url = str(url).strip() if pd.notna(url) else ""
    if url:
        return url
    return fallback or "https://placehold.co/1200x700?text=TourMate"

def money(value):
    try:
        return f"{float(value):,.0f} VNĐ"
    except Exception:
        return "0 VNĐ"

def load_tours():
    return read_query("SELECT * FROM tours ORDER BY departure_date ASC")

def load_customers():
    return read_query("SELECT * FROM customers ORDER BY created_at DESC")

def load_bookings():
    return read_query("SELECT * FROM bookings ORDER BY created_at DESC")

def load_booking_history():
    return read_query("""
        SELECT
            b.id AS ID,
            b.created_at AS `Thời gian`,
            c.full_name AS `Khách hàng`,
            c.phone AS `Số điện thoại`,
            t.tour_name AS `Tên tour`,
            t.destination AS `Điểm đến`,
            b.quantity AS `Số khách`,
            b.total_price AS `Tổng tiền`,
            b.payment_status AS `Trạng thái`
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN tours t ON b.tour_id = t.id
        ORDER BY b.created_at DESC
    """)

# ============================================================
# 5. FREE CHATBOT - KHÔNG CẦN API KEY
# ============================================================

def chatbot_answer(question, tours_df):
    q = question.lower().strip()

    if not q:
        return "Em hãy nhập câu hỏi nhé 😊"

    if tours_df.empty:
        return "Hiện hệ thống chưa có tour. Em hãy tạo tour trước nhé."

    df = tours_df.copy()
    df["price_num"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)

    # Giá / rẻ / đắt
    if any(k in q for k in ["rẻ", "giá thấp", "dưới", "chi phí", "bao nhiêu tiền", "giá tour"]):
        import re
        nums = re.findall(r"\d+(?:[.,]\d+)?", q)
        threshold = None
        if nums:
            raw = nums[0].replace(",", ".")
            try:
                threshold = float(raw)
                if "triệu" in q:
                    threshold *= 1_000_000
                elif threshold < 1000:
                    threshold *= 1_000_000
            except Exception:
                pass

        if threshold:
            result = df[df["price_num"] <= threshold].sort_values("price_num")
            if result.empty:
                return f"Không tìm thấy tour có giá từ {money(threshold)} trở xuống."
        else:
            result = df.sort_values("price_num").head(5)

        lines = ["💰 Các tour phù hợp về giá:"]
        for _, r in result.head(5).iterrows():
            lines.append(f"• {r['tour_name']} – {r['destination']} – {money(r['price_num'])}")
        return "\n".join(lines)

    # Destination
    destinations = sorted(
        [str(x) for x in df["destination"].dropna().unique()],
        key=len,
        reverse=True,
    )
    for dest in destinations:
        if dest.lower() in q:
            result = df[df["destination"].astype(str).str.lower() == dest.lower()]
            lines = [f"📍 Tour tại {dest}:"]
            for _, r in result.head(6).iterrows():
                lines.append(
                    f"• {r['tour_name']} – {r['duration']} ngày – {money(r['price_num'])}"
                )
            return "\n".join(lines)

    # Upcoming
    if any(k in q for k in ["sắp khởi hành", "gần nhất", "khởi hành", "ngày nào"]):
        result = df[df["departure_date"].notna()].sort_values("departure_date").head(5)
        lines = ["📅 Các tour sắp khởi hành:"]
        for _, r in result.iterrows():
            lines.append(
                f"• {r['tour_name']} – {r['departure_date']} – {r['destination']}"
            )
        return "\n".join(lines)

    # Family/group
    if any(k in q for k in ["gia đình", "nhóm", "4 người", "5 người", "6 người"]):
        result = df[df["max_people"].fillna(0) >= 10].sort_values("price_num").head(5)
        lines = ["👨‍👩‍👧‍👦 Một số tour phù hợp cho nhóm/gia đình:"]
        for _, r in result.iterrows():
            lines.append(
                f"• {r['tour_name']} – tối đa {int(r['max_people'])} khách – {money(r['price_num'])}"
            )
        return "\n".join(lines)

    if any(k in q for k in ["có tour nào", "tour nào", "danh sách tour", "tour hiện có"]):
        result = df.sort_values("departure_date").head(8)
        lines = ["🚌 Các tour hiện có:"]
        for _, r in result.iterrows():
            lines.append(f"• {r['tour_name']} – {r['destination']} – {money(r['price_num'])}")
        return "\n".join(lines)

    if any(k in q for k in ["xin chào", "hello", "hi", "chào"]):
        return (
            "Xin chào 👋 Mình là TourMate AI.\n\n"
            "Mình có thể giúp em tìm tour, xem giá, điểm đến và ngày khởi hành.\n"
            "Ví dụ: “Có tour Đà Lạt dưới 4 triệu không?”"
        )

    return (
        "🤖 Mình có thể hỗ trợ:\n"
        "• Tìm tour theo điểm đến\n"
        "• Xem giá tour\n"
        "• Tìm tour dưới một mức giá\n"
        "• Xem tour sắp khởi hành\n"
        "• Gợi ý tour cho nhóm/gia đình\n\n"
        "Ví dụ: “Có tour Phú Quốc không?”"
    )

def chatbot_widget():
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Xin chào 👋 Mình là **TourMate AI**.\n\n"
                    "Mình có thể tra cứu các tour đang có trong hệ thống."
                ),
            }
        ]

    tours_df = load_tours()

    st.markdown("### 🤖 TourMate AI")
    st.caption("Trợ lý miễn phí • Tra cứu trực tiếp dữ liệu tour trong MySQL")

    for msg in st.session_state.chat_messages[-8:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Hỏi về tour, giá, điểm đến...", key="tourmate_chat")
    if prompt:
        st.session_state.chat_messages.append(
            {"role": "user", "content": prompt}
        )
        answer = chatbot_answer(prompt, tours_df)
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": answer}
        )
        st.rerun()

# ============================================================
# 6. SIDEBAR
# ============================================================

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

st.sidebar.markdown("## ✈️ TOURMATE")
st.sidebar.caption("Smart Tour Management System")

page = st.sidebar.radio(
    "📋 Chọn chức năng",
    [
        "🏠 Tổng quan",
        "🌎 Khám phá điểm đến",
        "🚌 Quản lý Tour",
        "👤 Khách hàng",
        "📋 Đặt Tour",
        "🧾 Hóa đơn",
        "🤖 TourMate AI",
        "🔑 Admin",
    ],
)

st.sidebar.markdown("---")
st.sidebar.success("🟢 MySQL đang kết nối")
st.sidebar.caption("BVU - Quản trị dịch vụ du lịch và lữ hành")

# ============================================================
# 7. TỔNG QUAN
# ============================================================

if page == "🏠 Tổng quan":
    st.markdown("""
    <div class="hero">
        <h1>✈️ TourMate</h1>
        <p>Hệ thống quản lý tour trọn gói • khách hàng • booking • thanh toán • doanh thu</p>
    </div>
    """, unsafe_allow_html=True)

    df_tours = load_tours()
    df_customers = load_customers()
    df_bookings = load_bookings()

    revenue = (
        pd.to_numeric(df_bookings["total_price"], errors="coerce").fillna(0).sum()
        if not df_bookings.empty else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🚌 Tổng số tour", len(df_tours))
    c2.metric("👤 Khách hàng", len(df_customers))
    c3.metric("🎫 Booking", len(df_bookings))
    c4.metric("💰 Doanh thu", money(revenue))

    st.markdown("---")
    st.markdown('<div class="section-title">🌎 Tour đang có</div>', unsafe_allow_html=True)

    if df_tours.empty:
        st.info("📭 Chưa có tour nào. Hãy vào Quản lý Tour để tạo tour.")
    else:
        cols = st.columns(3)
        for i, (_, tour) in enumerate(df_tours.iterrows()):
            with cols[i % 3]:
                image = safe_image(
                    tour.get("image_url"),
                    DEFAULT_IMAGES.get(str(tour["destination"]), None),
                )
                st.markdown('<div class="tour-card">', unsafe_allow_html=True)
                try:
                    st.image(image, use_container_width=True)
                except Exception:
                    st.image("https://placehold.co/1200x700?text=TourMate", use_container_width=True)

                st.markdown('<div class="tour-card-body">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="tour-name">🚌 {tour["tour_name"]}</div>',
                    unsafe_allow_html=True,
                )
                st.write(f"📍 **{tour['destination']}**")
                st.write(f"📅 {tour['departure_date']} • ⏱️ {tour['duration']} ngày")
                st.markdown(
                    f'<div class="price">{money(tour["price"])}/khách</div>',
                    unsafe_allow_html=True,
                )

                if pd.notna(tour.get("description")):
                    desc = str(tour["description"])
                    st.caption(desc[:130] + ("..." if len(desc) > 130 else ""))
                st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-title">💡 Bạn có thể làm gì?</div>', unsafe_allow_html=True)

    a, b, c = st.columns(3)
    with a:
        st.info("🚌 **Quản lý Tour**\n\nTạo tour, lịch trình, giá, khách sạn, HDV và hình ảnh.")
    with b:
        st.info("🎫 **Đặt Tour**\n\nChọn khách hàng, kiểm tra số chỗ và tính tổng tiền tự động.")
    with c:
        st.info("🤖 **TourMate AI**\n\nTra cứu tour bằng ngôn ngữ tự nhiên, không cần API trả phí.")

# ============================================================
# 8. KHÁM PHÁ ĐIỂM ĐẾN
# ============================================================

elif page == "🌎 Khám phá điểm đến":
    st.title("🌎 KHÁM PHÁ ĐIỂM ĐẾN")
    st.caption("Các điểm đến nổi bật trong hệ thống TourMate")

    df = load_tours()

    destinations = list(DESTINATION_INFO.keys())
    if not df.empty:
        for d in df["destination"].dropna().astype(str).unique():
            if d not in destinations:
                destinations.append(d)

    cols = st.columns(3)
    for i, dest in enumerate(destinations):
        icon, description = DESTINATION_INFO.get(
            dest, ("📍", f"Khám phá các chương trình tour tại {dest}.")
        )

        count = 0 if df.empty else int(
            (df["destination"].astype(str).str.lower() == dest.lower()).sum()
        )

        image = DEFAULT_IMAGES.get(dest, "https://placehold.co/1200x700?text=Destination")

        with cols[i % 3]:
            st.markdown('<div class="destination-card">', unsafe_allow_html=True)
            st.image(image, use_container_width=True)
            st.markdown(f"### {icon} {dest}")
            st.caption(description)
            st.write(f"🚌 **{count}** chương trình tour")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    selected = st.selectbox("🔎 Xem tour tại điểm đến", ["Tất cả"] + destinations)

    if selected == "Tất cả":
        filtered = df
    else:
        filtered = df[df["destination"].astype(str).str.lower() == selected.lower()]

    if filtered.empty:
        st.info("Chưa có tour tại điểm đến này.")
    else:
        for _, tour in filtered.iterrows():
            with st.expander(f"🚌 {tour['tour_name']} — {tour['destination']}"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image(
                        safe_image(
                            tour.get("image_url"),
                            DEFAULT_IMAGES.get(str(tour["destination"])),
                        ),
                        use_container_width=True,
                    )
                with c2:
                    st.write(f"📅 Khởi hành: **{tour['departure_date']}**")
                    st.write(f"🏠 Kết thúc: **{tour['return_date']}**")
                    st.write(f"⏱️ Thời gian: **{tour['duration']} ngày**")
                    st.write(f"💰 Giá: **{money(tour['price'])}**")
                    st.write(f"🚌 Phương tiện: **{tour['transport']}**")
                    st.write(f"🏨 Khách sạn: **{tour['hotel']}**")
                    st.write(f"🍽️ Ăn uống: **{tour['meals']}**")
                    if pd.notna(tour.get("description")):
                        st.write(tour["description"])

# ============================================================
# 9. QUẢN LÝ TOUR
# ============================================================

elif page == "🚌 Quản lý Tour":
    st.title("🚌 QUẢN LÝ TOUR TRỌN GÓI")

    tab1, tab2 = st.tabs(["➕ Tạo Tour", "📋 Danh sách Tour"])

    with tab1:
        st.subheader("➕ Tạo chương trình tour mới")

        with st.form("create_tour_form", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                tour_name = st.text_input(
                    "🏷️ Tên tour",
                    placeholder="Tour Đà Lạt 3 ngày 2 đêm",
                )
                destination = st.text_input(
                    "📍 Điểm đến",
                    placeholder="Đà Lạt",
                )
                departure_date = st.date_input(
                    "🚌 Ngày khởi hành",
                    date.today(),
                )
                return_date = st.date_input(
                    "🏠 Ngày kết thúc",
                    date.today(),
                )
                duration = st.number_input(
                    "📅 Số ngày",
                    min_value=1,
                    value=3,
                    step=1,
                )
                price = st.number_input(
                    "💰 Giá tour / khách",
                    min_value=0,
                    value=3000000,
                    step=100000,
                )

            with c2:
                max_people = st.number_input(
                    "👥 Số khách tối đa",
                    min_value=1,
                    value=30,
                    step=1,
                )
                transport = st.selectbox(
                    "🚌 Phương tiện",
                    [
                        "Xe du lịch",
                        "Máy bay",
                        "Tàu hỏa",
                        "Tàu cao tốc",
                        "Xe + máy bay",
                        "Khác",
                    ],
                )
                hotel = st.text_input(
                    "🏨 Khách sạn",
                    placeholder="Khách sạn 3 sao",
                )
                meals = st.text_input(
                    "🍽️ Ăn uống",
                    placeholder="5 bữa chính + 2 bữa sáng",
                )
                tour_guide = st.text_input(
                    "🧑‍💼 Hướng dẫn viên",
                    placeholder="Nguyễn Văn A",
                )
                image_url = st.text_input(
                    "🖼️ Link ảnh tour",
                    placeholder="https://images.unsplash.com/...",
                )

            description = st.text_area(
                "📝 Nội dung / lịch trình tour",
                placeholder="Mô tả lịch trình và dịch vụ...",
            )

            st.caption(
                "💡 Có thể dùng link JPG/PNG/WEBP. Nếu để trống, hệ thống sẽ dùng ảnh mặc định theo điểm đến."
            )

            submit = st.form_submit_button(
                "💾 LƯU TOUR",
                use_container_width=True,
            )

        if submit:
            if not tour_name.strip():
                st.warning("⚠️ Vui lòng nhập tên tour.")
            elif not destination.strip():
                st.warning("⚠️ Vui lòng nhập điểm đến.")
            elif return_date < departure_date:
                st.error("❌ Ngày kết thúc không được trước ngày khởi hành.")
            else:
                success = execute_query(
                    """
                    INSERT INTO tours
                    (
                        tour_name, destination, departure_date, return_date,
                        duration, price, max_people, transport, hotel,
                        meals, tour_guide, description, image_url, created_at
                    )
                    VALUES
                    (
                        :tour_name, :destination, :departure_date, :return_date,
                        :duration, :price, :max_people, :transport, :hotel,
                        :meals, :tour_guide, :description, :image_url, :created_at
                    )
                    """,
                    {
                        "tour_name": tour_name.strip(),
                        "destination": destination.strip(),
                        "departure_date": departure_date,
                        "return_date": return_date,
                        "duration": duration,
                        "price": price,
                        "max_people": max_people,
                        "transport": transport,
                        "hotel": hotel.strip(),
                        "meals": meals.strip(),
                        "tour_guide": tour_guide.strip(),
                        "description": description.strip(),
                        "image_url": image_url.strip(),
                        "created_at": datetime.now(),
                    },
                )

                if success:
                    st.success("🎉 Tạo tour thành công!")
                    st.rerun()

    with tab2:
        st.subheader("📋 Danh sách tour")

        df = load_tours()

        if df.empty:
            st.info("📭 Chưa có tour.")
        else:
            search = st.text_input(
                "🔎 Tìm tour",
                placeholder="Tên tour, điểm đến...",
            )

            if search.strip():
                mask = (
                    df["tour_name"].astype(str).str.contains(search, case=False, na=False)
                    | df["destination"].astype(str).str.contains(search, case=False, na=False)
                )
                df = df[mask]

            for _, tour in df.iterrows():
                with st.expander(
                    f"🚌 {tour['tour_name']} — {tour['destination']}"
                ):
                    c1, c2 = st.columns([1, 2])

                    with c1:
                        st.image(
                            safe_image(
                                tour.get("image_url"),
                                DEFAULT_IMAGES.get(str(tour["destination"])),
                            ),
                            use_container_width=True,
                        )

                    with c2:
                        st.write(f"📍 Điểm đến: **{tour['destination']}**")
                        st.write(f"📅 Khởi hành: **{tour['departure_date']}**")
                        st.write(f"🏠 Kết thúc: **{tour['return_date']}**")
                        st.write(f"⏱️ Thời gian: **{tour['duration']} ngày**")
                        st.write(f"💰 Giá: **{money(tour['price'])}**")
                        st.write(f"👥 Tối đa: **{tour['max_people']} khách**")
                        st.write(f"🚌 Phương tiện: **{tour['transport']}**")
                        st.write(f"🏨 Khách sạn: **{tour['hotel']}**")
                        st.write(f"🍽️ Ăn uống: **{tour['meals']}**")
                        st.write(f"🧑‍💼 HDV: **{tour['tour_guide']}**")

                    if pd.notna(tour.get("description")):
                        st.markdown("**📝 Mô tả / lịch trình**")
                        st.write(tour["description"])

# ============================================================
# 10. KHÁCH HÀNG
# ============================================================

elif page == "👤 Khách hàng":
    st.title("👤 QUẢN LÝ KHÁCH HÀNG")

    tab1, tab2 = st.tabs(["➕ Thêm khách hàng", "📋 Danh sách khách hàng"])

    with tab1:
        with st.form("customer_form", clear_on_submit=True):
            full_name = st.text_input("👤 Họ và tên")
            phone = st.text_input("📱 Số điện thoại")
            email = st.text_input("📧 Email")
            address = st.text_input("🏠 Địa chỉ")

            submit = st.form_submit_button(
                "💾 LƯU KHÁCH HÀNG",
                use_container_width=True,
            )

        if submit:
            if not full_name.strip():
                st.warning("⚠️ Vui lòng nhập họ tên.")
            elif not phone.strip():
                st.warning("⚠️ Vui lòng nhập số điện thoại.")
            else:
                success = execute_query(
                    """
                    INSERT INTO customers
                    (full_name, phone, email, address, created_at)
                    VALUES
                    (:full_name, :phone, :email, :address, :created_at)
                    """,
                    {
                        "full_name": full_name.strip(),
                        "phone": phone.strip(),
                        "email": email.strip(),
                        "address": address.strip(),
                        "created_at": datetime.now(),
                    },
                )

                if success:
                    st.success("✅ Thêm khách hàng thành công!")
                    st.rerun()

    with tab2:
        df_customers = load_customers()

        if df_customers.empty:
            st.info("📭 Chưa có khách hàng.")
        else:
            display = df_customers.copy()
            display.columns = [
                "ID", "Họ tên", "Số điện thoại",
                "Email", "Địa chỉ", "Ngày tạo"
            ]
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
            )

# ============================================================
# 11. ĐẶT TOUR
# ============================================================

elif page == "📋 Đặt Tour":
    st.title("📋 ĐẶT TOUR TRỌN GÓI")

    customers = read_query("""
        SELECT id, full_name, phone
        FROM customers
        ORDER BY full_name
    """)

    tours = read_query("""
        SELECT id, tour_name, destination, departure_date,
               duration, price, max_people, image_url
        FROM tours
        WHERE departure_date >= CURRENT_DATE
        ORDER BY departure_date
    """)

    if customers.empty:
        st.warning("⚠️ Chưa có khách hàng. Hãy thêm khách hàng trước.")
    elif tours.empty:
        st.warning("⚠️ Chưa có tour sắp khởi hành.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            customer_options = [
                f"{row.full_name} - {row.phone}"
                for row in customers.itertuples()
            ]
            selected_customer = st.selectbox(
                "👤 Chọn khách hàng",
                customer_options,
            )
            customer_index = customer_options.index(selected_customer)
            customer_id = int(customers.iloc[customer_index]["id"])

        with c2:
            tour_options = [
                f"{row.tour_name} - {row.destination}"
                for row in tours.itertuples()
            ]
            selected_tour = st.selectbox("🚌 Chọn tour", tour_options)
            tour_index = tour_options.index(selected_tour)
            tour = tours.iloc[tour_index]
            tour_id = int(tour["id"])

        image = safe_image(
            tour.get("image_url"),
            DEFAULT_IMAGES.get(str(tour["destination"])),
        )
        st.image(image, use_container_width=True)

        st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)
        c1.info(f"📍 Điểm đến\n\n**{tour['destination']}**")
        c2.info(f"📅 Khởi hành\n\n**{tour['departure_date']}**")
        c3.info(f"⏱️ Thời gian\n\n**{tour['duration']} ngày**")

        tour_price = float(tour["price"])
        c4.info(f"💰 Giá tour\n\n**{money(tour_price)}**")

        booked_df = read_query(
            """
            SELECT COALESCE(SUM(quantity), 0) AS booked_people
            FROM bookings
            WHERE tour_id = :tour_id
            """,
            {"tour_id": tour_id},
        )

        booked_people = int(booked_df.iloc[0]["booked_people"])
        max_people = int(tour["max_people"])
        remaining = max_people - booked_people

        st.metric("🪑 Số chỗ còn lại", f"{remaining} / {max_people}")

        if remaining <= 0:
            st.error("❌ Tour đã đủ số lượng khách.")
        else:
            quantity = st.number_input(
                "👥 Số lượng khách",
                min_value=1,
                max_value=remaining,
                value=1,
                step=1,
            )

            total_price = tour_price * quantity

            st.metric("💰 TỔNG TIỀN", money(total_price))

            payment_status = st.selectbox(
                "💳 Trạng thái thanh toán",
                ["Chưa thanh toán", "Đã đặt cọc", "Đã thanh toán"],
            )

            if st.button(
                "🎫 XÁC NHẬN ĐẶT TOUR",
                use_container_width=True,
            ):
                success = execute_query(
                    """
                    INSERT INTO bookings
                    (
                        created_at, customer_id, tour_id,
                        quantity, total_price, payment_status
                    )
                    VALUES
                    (
                        :created_at, :customer_id, :tour_id,
                        :quantity, :total_price, :payment_status
                    )
                    """,
                    {
                        "created_at": datetime.now(),
                        "customer_id": customer_id,
                        "tour_id": tour_id,
                        "quantity": quantity,
                        "total_price": total_price,
                        "payment_status": payment_status,
                    },
                )

                if success:
                    st.success("🎉 Đặt tour thành công!")
                    st.success(f"💰 Tổng tiền: {money(total_price)}")
                    st.balloons()
                    st.rerun()

# ============================================================
# 12. HÓA ĐƠN
# ============================================================

elif page == "🧾 Hóa đơn":
    st.title("🧾 QUẢN LÝ HÓA ĐƠN")

    df_history = load_booking_history()

    if df_history.empty:
        st.info("📭 Hệ thống chưa có booking nào.")
    else:
        df_history["Tổng tiền"] = pd.to_numeric(
            df_history["Tổng tiền"], errors="coerce"
        ).fillna(0)

        total_revenue = df_history["Tổng tiền"].sum()
        total_people = df_history["Số khách"].sum()
        paid_revenue = df_history[
            df_history["Trạng thái"] == "Đã thanh toán"
        ]["Tổng tiền"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Tổng giá trị booking", money(total_revenue))
        c2.metric("👥 Tổng số khách", int(total_people))
        c3.metric("✅ Đã thanh toán", money(paid_revenue))

        st.markdown("---")
        st.subheader("📋 Danh sách booking")

        st.dataframe(
            df_history,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("💳 Cập nhật trạng thái thanh toán")

        booking_ids = df_history["ID"].tolist()
        selected_booking = st.selectbox("Chọn ID booking", booking_ids)

        new_status = st.selectbox(
            "Trạng thái mới",
            ["Chưa thanh toán", "Đã đặt cọc", "Đã thanh toán"],
        )

        if st.button(
            "💾 CẬP NHẬT THANH TOÁN",
            use_container_width=True,
        ):
            success = execute_query(
                """
                UPDATE bookings
                SET payment_status = :status
                WHERE id = :booking_id
                """,
                {
                    "status": new_status,
                    "booking_id": int(selected_booking),
                },
            )

            if success:
                st.success("✅ Cập nhật trạng thái thành công!")
                st.rerun()

# ============================================================
# 13. TOURMATE AI
# ============================================================

elif page == "🤖 TourMate AI":
    st.title("🤖 TOURMATE AI")
    st.markdown(
        '<div class="chat-note">'
        '💡 Đây là chatbot miễn phí, không cần API key. '
        'Nó đọc dữ liệu tour trực tiếp từ MySQL của app.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("🗑️ Xóa cuộc trò chuyện"):
        st.session_state.chat_messages = []
        st.rerun()

    chatbot_widget()

# ============================================================
# 14. ADMIN
# ============================================================

elif page == "🔑 Admin":
    st.title("🔑 TRANG QUẢN TRỊ")

    if not st.session_state.admin_logged_in:
        with st.form("admin_login"):
            password = st.text_input(
                "🔐 Mật khẩu quản trị",
                type="password",
            )
            login = st.form_submit_button("🔑 ĐĂNG NHẬP")

        if login:
            if password == "123456":
                st.session_state.admin_logged_in = True
                st.success("✅ Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác.")

        st.stop()

    c1, c2 = st.columns([5, 1])
    with c1:
        st.success("🟢 Quyền quản trị viên đã được xác thực.")
    with c2:
        if st.button("🔒 Đăng xuất"):
            st.session_state.admin_logged_in = False
            st.rerun()

    tab1, tab2, tab3 = st.tabs(
        ["🚌 Danh sách Tour", "💰 Doanh thu & Booking", "📊 Phân tích"]
    )

    with tab1:
        st.subheader("🚌 Danh sách chương trình tour")
        df_tours = load_tours()

        if df_tours.empty:
            st.info("📭 Chưa có tour.")
        else:
            display = df_tours.copy()
            display.columns = [
                "ID", "Tên tour", "Điểm đến", "Khởi hành",
                "Kết thúc", "Số ngày", "Giá", "Số khách tối đa",
                "Phương tiện", "Khách sạn", "Ăn uống", "HDV",
                "Mô tả", "Ảnh", "Ngày tạo"
            ]
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
            )

    with tab2:
        st.subheader("💰 Doanh thu & lịch sử booking")

        df_history = load_booking_history()

        if df_history.empty:
            st.info("📭 Chưa có booking.")
        else:
            df_history["Tổng tiền"] = pd.to_numeric(
                df_history["Tổng tiền"], errors="coerce"
            ).fillna(0)

            total_revenue = df_history["Tổng tiền"].sum()
            total_people = df_history["Số khách"].sum()
            total_bookings = len(df_history)

            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Tổng doanh thu", money(total_revenue))
            c2.metric("🎫 Tổng booking", total_bookings)
            c3.metric("👥 Tổng khách", int(total_people))

            st.markdown("---")
            st.subheader("📅 Doanh thu theo ngày")

            df_history["Thời gian"] = pd.to_datetime(df_history["Thời gian"])
            df_history["Ngày"] = df_history["Thời gian"].dt.date

            daily_revenue = (
                df_history.groupby("Ngày")["Tổng tiền"]
                .sum()
                .reset_index()
            )

            st.bar_chart(
                daily_revenue.set_index("Ngày")["Tổng tiền"]
            )

            st.markdown("---")
            st.subheader("📋 Lịch sử booking")
            st.dataframe(
                df_history,
                use_container_width=True,
                hide_index=True,
            )

    with tab3:
        st.subheader("📊 Thống kê & phân tích")

        df_anal = load_booking_history()

        if df_anal.empty:
            st.info("📭 Chưa có dữ liệu để phân tích.")
        else:
            df_anal["Tổng tiền"] = pd.to_numeric(
                df_anal["Tổng tiền"], errors="coerce"
            ).fillna(0)

            df_anal["Số khách"] = pd.to_numeric(
                df_anal["Số khách"], errors="coerce"
            ).fillna(0)

            tour_quantity = (
                df_anal.groupby("Tên tour")["Số khách"]
                .sum()
                .reset_index()
            )

            st.write("### 🚌 Số khách theo từng tour")
            st.bar_chart(
                tour_quantity.set_index("Tên tour")["Số khách"]
            )

            tour_revenue = (
                df_anal.groupby("Tên tour")["Tổng tiền"]
                .sum()
                .reset_index()
            )

            st.write("### 💰 Doanh thu theo tour")
            st.bar_chart(
                tour_revenue.set_index("Tên tour")["Tổng tiền"]
            )

            destination_quantity = (
                df_anal.groupby("Điểm đến")["Số khách"]
                .sum()
                .reset_index()
            )

            st.write("### 📍 Số khách theo điểm đến")
            st.dataframe(
                destination_quantity,
                use_container_width=True,
                hide_index=True,
            )

            st.write("### 📊 Bảng doanh thu theo tour")
            display_revenue = tour_revenue.copy()
            display_revenue["Tổng tiền"] = display_revenue[
                "Tổng tiền"
            ].apply(money)

            st.dataframe(
                display_revenue,
                use_container_width=True,
                hide_index=True,
            )

# ============================================================
# 15. FOOTER
# ============================================================

st.markdown(
    '<div class="footer">'
    '✈️ <b>TourMate – Smart Tour Management System</b><br>'
    'BVU • Quản trị dịch vụ du lịch và lữ hành'
    '</div>',
    unsafe_allow_html=True,
)
