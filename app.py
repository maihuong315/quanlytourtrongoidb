import pandas as pd
import streamlit as st

from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# 1. CẤU HÌNH STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Quản Lý Tour Trọn Gói",
    page_icon="✈️",
    layout="wide"
)


# ============================================================
# 2. KẾT NỐI AIVEN MYSQL
# ============================================================

DB = {
    "user": "avnadmin",
    "password": "DAN_PASSWORD_AIVEN_CUA_EM",
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
    database=DB["database"]
)


# ============================================================
# 3. DATABASE ENGINE
# ============================================================

@st.cache_resource
def get_db_engine():

    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            "connect_timeout": 15
        }
    )


# ============================================================
# 4. KIỂM TRA DATABASE
# ============================================================

def test_database_connection():

    try:

        engine = get_db_engine()

        with engine.connect() as conn:

            conn.execute(
                text("SELECT 1")
            )

        return True, "Kết nối MySQL thành công."

    except Exception as e:

        return False, str(e)


db_connected, db_message = test_database_connection()


# ============================================================
# 5. CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 38px;
        font-weight: 800;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 27px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    .tour-name {
        font-size: 21px;
        font-weight: 700;
        margin-top: 8px;
    }

    .tour-card {
        padding: 10px;
        border-radius: 12px;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 6. KIỂM TRA KẾT NỐI MYSQL
# ============================================================

with st.expander("🔧 Kiểm tra kết nối MySQL"):

    st.write("**Host:**", DB["host"])
    st.write("**Port:**", DB["port"])
    st.write("**Database:**", DB["database"])
    st.write("**User:**", DB["user"])

    if db_connected:

        st.success(
            "🟢 MySQL đã kết nối thành công."
        )

    else:

        st.error(
            "🔴 Không thể kết nối MySQL."
        )

        st.code(db_message)


if not db_connected:

    st.stop()


# ============================================================
# 7. TẠO DATABASE
# ============================================================

def init_db():

    engine = get_db_engine()

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

        itinerary TEXT,

        included TEXT,

        excluded TEXT,

        notes TEXT,

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

        FOREIGN KEY (customer_id)
            REFERENCES customers(id),

        FOREIGN KEY (tour_id)
            REFERENCES tours(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """


    with engine.begin() as conn:

        conn.exec_driver_sql(
            create_tours
        )

        conn.exec_driver_sql(
            create_customers
        )

        conn.exec_driver_sql(
            create_bookings
        )


try:

    init_db()

except Exception as e:

    st.error(
        "❌ Không thể khởi tạo Database."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# 8. ĐẢM BẢO CÁC CỘT NỘI DUNG TOUR TỒN TẠI
# ============================================================

try:

    engine = get_db_engine()

    tour_content_columns = {
        "image_url": "TEXT",
        "itinerary": "TEXT",
        "included": "TEXT",
        "excluded": "TEXT",
        "notes": "TEXT"
    }

    with engine.begin() as conn:

        for column_name, column_type in tour_content_columns.items():

            result = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'tours'
                    AND COLUMN_NAME = :column_name
                    """
                ),
                {
                    "column_name": column_name
                }
            )

            exists = result.scalar()

            if not exists:

                conn.exec_driver_sql(
                    f"""
                    ALTER TABLE tours
                    ADD COLUMN {column_name} {column_type}
                    """
                )

except Exception as e:

    st.warning(
        "⚠️ Không thể cập nhật các cột nội dung tour."
    )

    st.code(str(e))


# ============================================================
# 9. HÀM ĐỌC DATABASE
# ============================================================

def read_query(sql, params=None):

    try:

        engine = get_db_engine()

        with engine.connect() as conn:

            return pd.read_sql(
                text(sql),
                conn,
                params=params or {}
            )

    except Exception as e:

        st.error(
            "❌ Lỗi đọc dữ liệu."
        )

        st.code(str(e))

        return pd.DataFrame()


# ============================================================
# 10. HÀM GHI DATABASE
# ============================================================

def execute_query(sql, params=None):

    try:

        engine = get_db_engine()

        with engine.begin() as conn:

            conn.execute(
                text(sql),
                params or {}
            )

        return True

    except Exception as e:

        st.error(
            "❌ Lỗi lưu dữ liệu."
        )

        st.code(str(e))

        return False


# ============================================================
# 11. THÊM 3 TOUR MẪU
# ============================================================

def add_sample_tours():

    try:

        engine = get_db_engine()

        with engine.begin() as conn:

            existing_tours = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM tours
                    WHERE tour_name IN (
                        'Vũng Tàu 2N1Đ - Biển xanh, núi đẹp',
                        'Đà Lạt 3N2Đ - Thành phố ngàn hoa',
                        'Phú Quốc 3N2Đ - Thiên đường đảo ngọc'
                    )
                    """
                )
            ).scalar()


            if existing_tours > 0:

                return


            tours = [

                # ==================================================
                # TOUR 1 - VŨNG TÀU
                # ==================================================

                {
                    "tour_name":
                        "Vũng Tàu 2N1Đ - Biển xanh, núi đẹp",

                    "destination":
                        "Vũng Tàu",

                    "departure_date":
                        "2026-10-10",

                    "return_date":
                        "2026-10-11",

                    "duration":
                        2,

                    "price":
                        1890000,

                    "max_people":
                        30,

                    "transport":
                        "Xe du lịch",

                    "hotel":
                        "Khách sạn 3 sao",

                    "meals":
                        "3 bữa chính + 1 bữa sáng",

                    "tour_guide":
                        "Hướng dẫn viên chuyên nghiệp",

                    "image_url":
                        "",

                    "description":
                        """
Tour Vũng Tàu 2 ngày 1 đêm mang đến hành trình
nghỉ dưỡng kết hợp tham quan những điểm nổi bật
của thành phố biển. Du khách có thời gian thư giãn,
khám phá cảnh đẹp và thưởng thức đặc sản địa phương.
""",

                    "itinerary":
                        """
NGÀY 1: TP.HCM - VŨNG TÀU

07:00 - Tập trung và khởi hành đi Vũng Tàu.

09:30 - Tham quan khu vực Bãi Sau.

11:30 - Dùng bữa trưa tại nhà hàng địa phương.

13:30 - Nhận phòng khách sạn và nghỉ ngơi.

15:30 - Tham quan Tượng Chúa Kitô Vua.

17:30 - Tự do tắm biển, vui chơi và chụp ảnh.

18:30 - Dùng bữa tối.

20:00 - Tự do khám phá Vũng Tàu về đêm.


NGÀY 2: VŨNG TÀU - TP.HCM

06:30 - Dùng bữa sáng tại khách sạn.

07:30 - Tham quan Mũi Nghinh Phong.

09:30 - Tham quan và mua đặc sản địa phương.

11:00 - Trả phòng.

11:30 - Dùng bữa trưa.

13:00 - Khởi hành về TP.HCM.

15:30 - Kết thúc chương trình.
""",

                    "included":
                        """
- Xe du lịch đưa đón theo chương trình.
- Khách sạn tiêu chuẩn 3 sao.
- Các bữa ăn theo chương trình.
- Vé tham quan các điểm có trong lịch trình.
- Hướng dẫn viên.
- Nước uống trên xe.
- Bảo hiểm du lịch.
""",

                    "excluded":
                        """
- Chi phí cá nhân.
- Đồ uống gọi thêm tại nhà hàng.
- Các dịch vụ ngoài chương trình.
- Tiền mua đặc sản và quà lưu niệm.
- Chi phí phát sinh do yêu cầu riêng của khách.
""",

                    "notes":
                        """
- Có mặt đúng giờ tại điểm tập trung.
- Mang theo CCCD hoặc giấy tờ tùy thân.
- Chuẩn bị trang phục thoải mái, phù hợp tham quan biển.
- Lịch trình có thể thay đổi tùy tình hình thực tế
  nhưng vẫn đảm bảo các điểm chính.
"""
                },


                # ==================================================
                # TOUR 2 - ĐÀ LẠT
                # ==================================================

                {
                    "tour_name":
                        "Đà Lạt 3N2Đ - Thành phố ngàn hoa",

                    "destination":
                        "Đà Lạt",

                    "departure_date":
                        "2026-11-05",

                    "return_date":
                        "2026-11-07",

                    "duration":
                        3,

                    "price":
                        3290000,

                    "max_people":
                        30,

                    "transport":
                        "Xe du lịch",

                    "hotel":
                        "Khách sạn 3 sao",

                    "meals":
                        "5 bữa chính + 2 bữa sáng",

                    "tour_guide":
                        "Hướng dẫn viên",

                    "image_url":
                        "",

                    "description":
                        """
Hành trình khám phá Đà Lạt với không khí mát mẻ,
cảnh quan thơ mộng và những địa điểm tham quan
nổi bật. Tour phù hợp cho nhóm bạn, gia đình và
du khách yêu thích thiên nhiên.
""",

                    "itinerary":
                        """
NGÀY 1: TP.HCM - ĐÀ LẠT

05:30 - Tập trung và khởi hành đi Đà Lạt.

11:30 - Dùng bữa trưa.

14:00 - Nhận phòng khách sạn.

15:00 - Tham quan Quảng trường Lâm Viên.

16:30 - Tham quan Hồ Xuân Hương.

18:30 - Dùng bữa tối.

19:30 - Tự do khám phá chợ đêm Đà Lạt.


NGÀY 2: KHÁM PHÁ ĐÀ LẠT

07:00 - Dùng bữa sáng.

08:00 - Tham quan Thiền viện Trúc Lâm.

10:00 - Tham quan khu vực hồ Tuyền Lâm.

12:00 - Dùng bữa trưa.

14:00 - Tham quan một điểm du lịch nổi bật.

17:00 - Về khách sạn nghỉ ngơi.

18:30 - Dùng bữa tối.

20:00 - Tự do khám phá thành phố.


NGÀY 3: ĐÀ LẠT - TP.HCM

07:00 - Dùng bữa sáng.

08:00 - Tham quan và mua đặc sản.

10:30 - Trả phòng.

11:00 - Dùng bữa trưa.

12:30 - Khởi hành về TP.HCM.

20:00 - Dự kiến kết thúc chương trình.
""",

                    "included":
                        """
- Xe du lịch theo chương trình.
- Khách sạn 3 sao.
- Các bữa ăn theo chương trình.
- Vé tham quan.
- Hướng dẫn viên.
- Nước uống.
- Bảo hiểm du lịch.
""",

                    "excluded":
                        """
- Chi phí cá nhân.
- Đồ uống ngoài chương trình.
- Vé các dịch vụ tự chọn.
- Chi phí mua sắm cá nhân.
- Các chi phí phát sinh ngoài chương trình.
""",

                    "notes":
                        """
- Đà Lạt có thời tiết thay đổi trong ngày,
  nên mang theo áo khoác.
- Mang giày dép thoải mái để thuận tiện di chuyển.
- Bảo quản tư trang cá nhân trong quá trình tham quan.
- Thời gian có thể điều chỉnh tùy tình hình
  giao thông và thời tiết.
"""
                },


                # ==================================================
                # TOUR 3 - PHÚ QUỐC
                # ==================================================

                {
                    "tour_name":
                        "Phú Quốc 3N2Đ - Thiên đường đảo ngọc",

                    "destination":
                        "Phú Quốc",

                    "departure_date":
                        "2026-12-12",

                    "return_date":
                        "2026-12-14",

                    "duration":
                        3,

                    "price":
                        4590000,

                    "max_people":
                        30,

                    "transport":
                        "Máy bay + xe du lịch",

                    "hotel":
                        "Khách sạn 4 sao",

                    "meals":
                        "5 bữa chính + 2 bữa sáng",

                    "tour_guide":
                        "Hướng dẫn viên",

                    "image_url":
                        "",

                    "description":
                        """
Tour Phú Quốc 3 ngày 2 đêm kết hợp nghỉ dưỡng
và khám phá thiên nhiên biển đảo. Du khách có cơ hội
tham quan các điểm nổi bật, thưởng thức hải sản
và tận hưởng không gian nghỉ dưỡng.
""",

                    "itinerary":
                        """
NGÀY 1: ĐẾN PHÚ QUỐC - KHÁM PHÁ ĐẢO

Buổi sáng - Đón khách tại sân bay.

11:30 - Dùng bữa trưa.

13:00 - Nhận phòng khách sạn.

15:00 - Tham quan một số điểm nổi bật trên đảo.

17:30 - Ngắm hoàng hôn.

18:30 - Dùng bữa tối.

20:00 - Tự do khám phá Phú Quốc về đêm.


NGÀY 2: KHÁM PHÁ BIỂN ĐẢO

07:00 - Dùng bữa sáng.

08:00 - Khởi hành tham quan khu vực biển đảo.

12:00 - Dùng bữa trưa.

13:30 - Tiếp tục chương trình tham quan và vui chơi.

17:00 - Trở về khách sạn.

18:30 - Dùng bữa tối.

20:00 - Tự do nghỉ ngơi.


NGÀY 3: PHÚ QUỐC - KẾT THÚC

07:00 - Dùng bữa sáng.

08:00 - Tự do nghỉ ngơi hoặc mua đặc sản.

10:30 - Trả phòng.

11:00 - Dùng bữa trưa.

12:30 - Di chuyển ra sân bay.

Kết thúc chương trình.
""",

                    "included":
                        """
- Xe đưa đón tại Phú Quốc.
- Khách sạn 4 sao.
- Các bữa ăn theo chương trình.
- Vé tham quan theo lịch trình.
- Hướng dẫn viên.
- Nước uống.
- Bảo hiểm du lịch.
""",

                    "excluded":
                        """
- Vé máy bay nếu không nằm trong giá tour.
- Chi phí cá nhân.
- Đồ uống ngoài chương trình.
- Các hoạt động vui chơi tự chọn.
- Chi phí mua sắm.
- Các chi phí phát sinh ngoài chương trình.
""",

                    "notes":
                        """
- Mang theo giấy tờ tùy thân.
- Chuẩn bị đồ bơi, kem chống nắng
  và trang phục phù hợp.
- Tuân thủ hướng dẫn an toàn khi tham gia
  các hoạt động trên biển.
- Lịch trình có thể thay đổi tùy điều kiện thời tiết.
"""
                }
            ]


            for tour in tours:

                conn.execute(
                    text(
                        """
                        INSERT INTO tours
                        (
                            tour_name,
                            destination,
                            departure_date,
                            return_date,
                            duration,
                            price,
                            max_people,
                            transport,
                            hotel,
                            meals,
                            tour_guide,
                            description,
                            image_url,
                            itinerary,
                            included,
                            excluded,
                            notes,
                            created_at
                        )

                        VALUES
                        (
                            :tour_name,
                            :destination,
                            :departure_date,
                            :return_date,
                            :duration,
                            :price,
                            :max_people,
                            :transport,
                            :hotel,
                            :meals,
                            :tour_guide,
                            :description,
                            :image_url,
                            :itinerary,
                            :included,
                            :excluded,
                            :notes,
                            :created_at
                        )
                        """
                    ),
                    {
                        **tour,
                        "created_at": datetime.now()
                    }
                )

    except Exception as e:

        st.warning(
            "⚠️ Không thể thêm tour mẫu."
        )

        st.code(str(e))


add_sample_tours()


# ============================================================
# 12. LỊCH SỬ BOOKING
# ============================================================

def load_booking_history():

    sql = """
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

    JOIN customers c
        ON b.customer_id = c.id

    JOIN tours t
        ON b.tour_id = t.id

    ORDER BY b.created_at DESC
    """

    return read_query(sql)


# ============================================================
# 13. SESSION STATE
# ============================================================

if "admin_logged_in" not in st.session_state:

    st.session_state.admin_logged_in = False


# ============================================================
# 14. SIDEBAR
# ============================================================

st.sidebar.title(
    "✈️ QUẢN LÝ TOUR"
)

st.sidebar.caption(
    "Hệ thống quản lý tour trọn gói"
)

page = st.sidebar.radio(
    "📋 Chọn chức năng",
    [
        "🏠 Tổng quan",
        "🚌 Quản lý Tour",
        "👤 Khách hàng",
        "📋 Đặt Tour",
        "🧾 Hóa đơn",
        "🔑 Admin"
    ]
)


# ============================================================
# 15. TRANG TỔNG QUAN
# ============================================================

if page == "🏠 Tổng quan":

    st.markdown(
        '<div class="main-title">'
        '✈️ HỆ THỐNG QUẢN LÝ TOUR TRỌN GÓI'
        '</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="sub-title">'
        'Quản lý tour • khách hàng • booking • thanh toán • doanh thu'
        '</div>',
        unsafe_allow_html=True
    )


    st.success(
        "🟢 Hệ thống đã kết nối MySQL"
    )


    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    df_tours = read_query(
        "SELECT * FROM tours ORDER BY departure_date"
    )

    df_customers = read_query(
        "SELECT * FROM customers"
    )

    df_bookings = read_query(
        "SELECT * FROM bookings"
    )


    # --------------------------------------------------------
    # THỐNG KÊ
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "🚌 Tổng số tour",
            len(df_tours)
        )


    with col2:

        st.metric(
            "👤 Khách hàng",
            len(df_customers)
        )


    with col3:

        st.metric(
            "📋 Booking",
            len(df_bookings)
        )


    with col4:

        if not df_bookings.empty:

            revenue = pd.to_numeric(
                df_bookings["total_price"],
                errors="coerce"
            ).fillna(0).sum()

        else:

            revenue = 0


        st.metric(
            "💰 Doanh thu",
            f"{revenue:,.0f} VNĐ"
        )


    st.markdown("---")


    # ========================================================
    # TOUR TỰ ĐỘNG TỪ MYSQL
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        '🌎 CÁC TOUR ĐANG CÓ'
        '</div>',
        unsafe_allow_html=True
    )


    if df_tours.empty:

        st.info(
            "📭 Chưa có tour nào trong hệ thống."
        )

    else:

        tour_cols = st.columns(3)


        for index, (_, tour) in enumerate(
            df_tours.iterrows()
        ):

            with tour_cols[index % 3]:

                st.markdown(
                    '<div class="tour-card">',
                    unsafe_allow_html=True
                )


                image_url = tour.get(
                    "image_url"
                )


                if (
                    pd.notna(image_url)
                    and str(image_url).strip()
                ):

                    try:

                        st.image(
                            str(image_url).strip(),
                            use_container_width=True
                        )

                    except Exception:

                        st.info(
                            "🖼️ Không tải được ảnh tour."
                        )

                else:

                    st.info(
                        "🖼️ Tour chưa có ảnh."
                    )


                st.markdown(
                    f"### 🚌 {tour['tour_name']}"
                )


                st.write(
                    f"📍 **{tour['destination']}**"
                )


                st.write(
                    f"📅 Khởi hành: "
                    f"**{tour['departure_date']}**"
                )


                st.write(
                    f"⏱️ Thời gian: "
                    f"**{tour['duration']} ngày**"
                )


                st.write(
                    f"💰 Giá: "
                    f"**{float(tour['price']):,.0f} VNĐ/khách**"
                )


                if pd.notna(
                    tour.get("transport")
                ):

                    st.write(
                        f"🚌 Phương tiện: "
                        f"{tour['transport']}"
                    )


                if pd.notna(
                    tour.get("hotel")
                ):

                    st.write(
                        f"🏨 Khách sạn: "
                        f"{tour['hotel']}"
                    )


                if pd.notna(
                    tour.get("description")
                ):

                    description = str(
                        tour["description"]
                    )

                    if len(description) > 150:

                        description = (
                            description[:150]
                            + "..."
                        )

                    st.caption(
                        description
                    )


                # Xem nội dung tour
                with st.expander(
                    "📖 Xem chương trình tour"
                ):

                    if pd.notna(
                        tour.get("itinerary")
                    ):

                        st.markdown(
                            "### 🗓️ Lịch trình"
                        )

                        st.text(
                            str(tour["itinerary"])
                        )


                    if pd.notna(
                        tour.get("included")
                    ):

                        st.markdown(
                            "### ✅ Dịch vụ bao gồm"
                        )

                        st.text(
                            str(tour["included"])
                        )


                    if pd.notna(
                        tour.get("excluded")
                    ):

                        st.markdown(
                            "### ❌ Dịch vụ không bao gồm"
                        )

                        st.text(
                            str(tour["excluded"])
                        )


                    if pd.notna(
                        tour.get("notes")
                    ):

                        st.markdown(
                            "### 📌 Lưu ý"
                        )

                        st.text(
                            str(tour["notes"])
                        )


                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )


    # ========================================================
    # BẢNG TOUR
    # ========================================================

    st.markdown("---")


    st.markdown(
        '<div class="section-title">'
        '📋 DANH SÁCH CHI TIẾT TOUR'
        '</div>',
        unsafe_allow_html=True
    )


    if not df_tours.empty:

        display = df_tours[
            [
                "id",
                "tour_name",
                "destination",
                "departure_date",
                "return_date",
                "duration",
                "price",
                "max_people"
            ]
        ].copy()


        display.columns = [
            "ID",
            "Tên tour",
            "Điểm đến",
            "Khởi hành",
            "Kết thúc",
            "Số ngày",
            "Giá tour",
            "Số khách tối đa"
        ]


        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 16. QUẢN LÝ TOUR
# ============================================================

elif page == "🚌 Quản lý Tour":

    st.title(
        "🚌 QUẢN LÝ TOUR TRỌN GÓI"
    )


    tab1, tab2 = st.tabs(
        [
            "➕ Tạo Tour",
            "📋 Danh sách Tour"
        ]
    )


    # ========================================================
    # TẠO TOUR
    # ========================================================

    with tab1:

        st.subheader(
            "➕ Tạo chương trình tour mới"
        )


        with st.form(
            "create_tour_form"
        ):

            col1, col2 = st.columns(2)


            with col1:

                tour_name = st.text_input(
                    "🏷️ Tên tour",
                    placeholder="Tour Đà Lạt 3 ngày 2 đêm"
                )


                destination = st.text_input(
                    "📍 Điểm đến",
                    placeholder="Đà Lạt"
                )


                departure_date = st.date_input(
                    "🚌 Ngày khởi hành",
                    date.today()
                )


                return_date = st.date_input(
                    "🏠 Ngày kết thúc",
                    date.today()
                )


                duration = st.number_input(
                    "📅 Số ngày",
                    min_value=1,
                    value=3,
                    step=1
                )


                price = st.number_input(
                    "💰 Giá tour / khách",
                    min_value=0,
                    value=3000000,
                    step=100000
                )


            with col2:

                max_people = st.number_input(
                    "👥 Số khách tối đa",
                    min_value=1,
                    value=30,
                    step=1
                )


                transport = st.selectbox(
                    "🚌 Phương tiện",
                    [
                        "Xe du lịch",
                        "Máy bay",
                        "Tàu hỏa",
                        "Tàu cao tốc",
                        "Xe + máy bay",
                        "Khác"
                    ]
                )


                hotel = st.text_input(
                    "🏨 Khách sạn",
                    placeholder="Khách sạn 3 sao"
                )


                meals = st.text_input(
                    "🍽️ Ăn uống",
                    placeholder="5 bữa chính + 2 bữa sáng"
                )


                tour_guide = st.text_input(
                    "🧑‍💼 Hướng dẫn viên",
                    placeholder="Nguyễn Văn A"
                )


                image_url = st.text_input(
                    "🖼️ Link ảnh tour",
                    placeholder="https://..."
                )


            # =================================================
            # NỘI DUNG TOUR
            # =================================================

            st.markdown("---")

            st.subheader(
                "📝 NỘI DUNG CHI TIẾT TOUR"
            )


            description = st.text_area(
                "📖 Giới thiệu tour",
                placeholder=(
                    "Giới thiệu tổng quan về tour, "
                    "điểm nổi bật, đối tượng phù hợp..."
                ),
                height=120
            )


            itinerary = st.text_area(
                "🗓️ Lịch trình chi tiết",
                placeholder="""NGÀY 1:
07:00 - Tập trung.
08:00 - Khởi hành.
12:00 - Dùng bữa trưa.
14:00 - Nhận phòng.
15:00 - Tham quan.

NGÀY 2:
07:00 - Ăn sáng.
08:00 - Tham quan.
12:00 - Ăn trưa.
14:00 - Tiếp tục chương trình.
17:00 - Kết thúc.""",
                height=250
            )


            included = st.text_area(
                "✅ Dịch vụ bao gồm",
                placeholder="""- Xe du lịch.
- Khách sạn.
- Các bữa ăn theo chương trình.
- Vé tham quan.
- Hướng dẫn viên.
- Nước uống.
- Bảo hiểm du lịch.""",
                height=160
            )


            excluded = st.text_area(
                "❌ Dịch vụ không bao gồm",
                placeholder="""- Chi phí cá nhân.
- Đồ uống ngoài chương trình.
- Chi phí mua sắm.
- Dịch vụ tự chọn.
- Chi phí phát sinh ngoài chương trình.""",
                height=130
            )


            notes = st.text_area(
                "📌 Lưu ý",
                placeholder="""- Mang theo CCCD/giấy tờ tùy thân.
- Có mặt đúng giờ.
- Chuẩn bị trang phục phù hợp.
- Lịch trình có thể thay đổi tùy tình hình thực tế.""",
                height=130
            )


            st.caption(
                "💡 Dán link ảnh JPG/PNG trực tiếp vào ô Link ảnh tour."
            )


            submit = st.form_submit_button(
                "💾 LƯU TOUR",
                use_container_width=True
            )


            if submit:

                if not tour_name.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập tên tour."
                    )


                elif not destination.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập điểm đến."
                    )


                elif return_date < departure_date:

                    st.error(
                        "❌ Ngày kết thúc không được trước ngày khởi hành."
                    )


                else:

                    success = execute_query(
                        """
                        INSERT INTO tours
                        (
                            tour_name,
                            destination,
                            departure_date,
                            return_date,
                            duration,
                            price,
                            max_people,
                            transport,
                            hotel,
                            meals,
                            tour_guide,
                            description,
                            image_url,
                            itinerary,
                            included,
                            excluded,
                            notes,
                            created_at
                        )

                        VALUES
                        (
                            :tour_name,
                            :destination,
                            :departure_date,
                            :return_date,
                            :duration,
                            :price,
                            :max_people,
                            :transport,
                            :hotel,
                            :meals,
                            :tour_guide,
                            :description,
                            :image_url,
                            :itinerary,
                            :included,
                            :excluded,
                            :notes,
                            :created_at
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
                            "hotel": hotel,
                            "meals": meals,
                            "tour_guide": tour_guide,
                            "description": description.strip(),
                            "image_url": image_url.strip(),
                            "itinerary": itinerary.strip(),
                            "included": included.strip(),
                            "excluded": excluded.strip(),
                            "notes": notes.strip(),
                            "created_at": datetime.now()
                        }
                    )


                    if success:

                        st.success(
                            "🎉 Tạo tour thành công!"
                        )

                        st.rerun()


    # ========================================================
    # DANH SÁCH TOUR
    # ========================================================

    with tab2:

        st.subheader(
            "📋 Danh sách tour"
        )


        df = read_query(
            """
            SELECT
                id,
                tour_name,
                destination,
                departure_date,
                return_date,
                duration,
                price,
                max_people,
                transport,
                hotel,
                meals,
                tour_guide,
                image_url,
                description,
                itinerary,
                included,
                excluded,
                notes
            FROM tours
            ORDER BY departure_date ASC
            """
        )


        if df.empty:

            st.info(
                "📭 Chưa có tour."
            )

        else:

            for _, tour in df.iterrows():

                with st.expander(
                    f"🚌 {tour['tour_name']} - {tour['destination']}"
                ):

                    col1, col2 = st.columns(
                        [1, 2]
                    )


                    with col1:

                        image_url = tour.get(
                            "image_url"
                        )


                        if (
                            pd.notna(image_url)
                            and str(image_url).strip()
                        ):

                            st.image(
                                str(image_url).strip(),
                                use_container_width=True
                            )

                        else:

                            st.info(
                                "🖼️ Chưa có ảnh"
                            )


                    with col2:

                        st.write(
                            f"📍 Điểm đến: **{tour['destination']}**"
                        )

                        st.write(
                            f"📅 Khởi hành: **{tour['departure_date']}**"
                        )

                        st.write(
                            f"🏠 Kết thúc: **{tour['return_date']}**"
                        )

                        st.write(
                            f"⏱️ Thời gian: **{tour['duration']} ngày**"
                        )

                        st.write(
                            f"💰 Giá: **{float(tour['price']):,.0f} VNĐ**"
                        )

                        st.write(
                            f"👥 Tối đa: **{tour['max_people']} khách**"
                        )

                        st.write(
                            f"🚌 Phương tiện: **{tour['transport']}**"
                        )

                        st.write(
                            f"🏨 Khách sạn: **{tour['hotel']}**"
                        )

                        st.write(
                            f"🍽️ Ăn uống: **{tour['meals']}**"
                        )

                        st.write(
                            f"🧑‍💼 Hướng dẫn viên: **{tour['tour_guide']}**"
                        )


                    if pd.notna(
                        tour.get("description")
                    ):

                        st.markdown(
                            "### 📖 Giới thiệu tour"
                        )

                        st.write(
                            tour["description"]
                        )


                    if pd.notna(
                        tour.get("itinerary")
                    ):

                        st.markdown(
                            "### 🗓️ Lịch trình chi tiết"
                        )

                        st.text(
                            str(tour["itinerary"])
                        )


                    if pd.notna(
                        tour.get("included")
                    ):

                        st.markdown(
                            "### ✅ Dịch vụ bao gồm"
                        )

                        st.text(
                            str(tour["included"])
                        )


                    if pd.notna(
                        tour.get("excluded")
                    ):

                        st.markdown(
                            "### ❌ Dịch vụ không bao gồm"
                        )

                        st.text(
                            str(tour["excluded"])
                        )


                    if pd.notna(
                        tour.get("notes")
                    ):

                        st.markdown(
                            "### 📌 Lưu ý"
                        )

                        st.text(
                            str(tour["notes"])
                        )


# ============================================================
# 17. KHÁCH HÀNG
# ============================================================

elif page == "👤 Khách hàng":

    st.title(
        "👤 QUẢN LÝ KHÁCH HÀNG"
    )


    tab1, tab2 = st.tabs(
        [
            "➕ Thêm khách hàng",
            "📋 Danh sách khách hàng"
        ]
    )


    with tab1:

        with st.form(
            "customer_form"
        ):

            full_name = st.text_input(
                "👤 Họ và tên"
            )


            phone = st.text_input(
                "📱 Số điện thoại"
            )


            email = st.text_input(
                "📧 Email"
            )


            address = st.text_input(
                "🏠 Địa chỉ"
            )


            submit = st.form_submit_button(
                "💾 LƯU KHÁCH HÀNG",
                use_container_width=True
            )


            if submit:

                if not full_name.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập họ tên."
                    )


                elif not phone.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập số điện thoại."
                    )


                else:

                    success = execute_query(
                        """
                        INSERT INTO customers
                        (
                            full_name,
                            phone,
                            email,
                            address,
                            created_at
                        )

                        VALUES
                        (
                            :full_name,
                            :phone,
                            :email,
                            :address,
                            :created_at
                        )
                        """,
                        {
                            "full_name": full_name.strip(),
                            "phone": phone.strip(),
                            "email": email.strip(),
                            "address": address.strip(),
                            "created_at": datetime.now()
                        }
                    )


                    if success:

                        st.success(
                            "✅ Thêm khách hàng thành công!"
                        )

                        st.rerun()


    with tab2:

        df_customers = read_query(
            """
            SELECT
                id,
                full_name,
                phone,
                email,
                address,
                created_at
            FROM customers
            ORDER BY created_at DESC
            """
        )


        if df_customers.empty:

            st.info(
                "📭 Chưa có khách hàng."
            )

        else:

            display = df_customers.copy()


            display.columns = [
                "ID",
                "Họ tên",
                "Số điện thoại",
                "Email",
                "Địa chỉ",
                "Ngày tạo"
            ]


            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# 18. ĐẶT TOUR
# ============================================================

elif page == "📋 Đặt Tour":

    st.title(
        "📋 ĐẶT TOUR TRỌN GÓI"
    )


    customers = read_query(
        """
        SELECT
            id,
            full_name,
            phone
        FROM customers
        ORDER BY full_name
        """
    )


    tours = read_query(
        """
        SELECT
            id,
            tour_name,
            destination,
            departure_date,
            duration,
            price,
            max_people,
            image_url,
            description,
            itinerary,
            included,
            excluded,
            notes
        FROM tours
        WHERE departure_date >= CURRENT_DATE
        ORDER BY departure_date
        """
    )


    if customers.empty:

        st.warning(
            "⚠️ Chưa có khách hàng. "
            "Hãy thêm khách hàng trước."
        )


    elif tours.empty:

        st.warning(
            "⚠️ Chưa có tour sắp khởi hành."
        )


    else:

        col1, col2 = st.columns(2)


        with col1:

            customer_options = [
                f"{row.full_name} - {row.phone}"
                for row in customers.itertuples()
            ]


            selected_customer = st.selectbox(
                "👤 Chọn khách hàng",
                customer_options
            )


            customer_index = customer_options.index(
                selected_customer
            )


            customer_id = int(
                customers.iloc[customer_index]["id"]
            )


        with col2:

            tour_options = [
                f"{row.tour_name} - {row.destination}"
                for row in tours.itertuples()
            ]


            selected_tour = st.selectbox(
                "🚌 Chọn tour",
                tour_options
            )


            tour_index = tour_options.index(
                selected_tour
            )


            tour = tours.iloc[tour_index]


            tour_id = int(
                tour["id"]
            )


        # ----------------------------------------------------
        # ẢNH TOUR
        # ----------------------------------------------------

        image_url = tour.get(
            "image_url"
        )


        if (
            pd.notna(image_url)
            and str(image_url).strip()
        ):

            st.image(
                str(image_url).strip(),
                use_container_width=True
            )


        # ----------------------------------------------------
        # THÔNG TIN TOUR
        # ----------------------------------------------------

        st.markdown("---")


        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.info(
                f"📍 Điểm đến\n\n"
                f"**{tour['destination']}**"
            )


        with col2:

            st.info(
                f"📅 Khởi hành\n\n"
                f"**{tour['departure_date']}**"
            )


        with col3:

            st.info(
                f"⏱️ Thời gian\n\n"
                f"**{tour['duration']} ngày**"
            )


        with col4:

            tour_price = float(
                tour["price"]
            )


            st.info(
                f"💰 Giá tour\n\n"
                f"**{tour_price:,.0f} VNĐ**"
            )


        # ====================================================
        # NỘI DUNG TOUR CHO KHÁCH XEM
        # ====================================================

        st.markdown("---")

        st.subheader(
            "📖 CHƯƠNG TRÌNH TOUR"
        )


        if pd.notna(
            tour.get("description")
        ):

            st.markdown(
                "### 📖 Giới thiệu"
            )

            st.write(
                tour["description"]
            )


        if pd.notna(
            tour.get("itinerary")
        ):

            st.markdown(
                "### 🗓️ Lịch trình"
            )

            st.text(
                str(tour["itinerary"])
            )


        if pd.notna(
            tour.get("included")
        ):

            st.markdown(
                "### ✅ Dịch vụ bao gồm"
            )

            st.text(
                str(tour["included"])
            )


        if pd.notna(
            tour.get("excluded")
        ):

            st.markdown(
                "### ❌ Dịch vụ không bao gồm"
            )

            st.text(
                str(tour["excluded"])
            )


        if pd.notna(
            tour.get("notes")
        ):

            st.markdown(
                "### 📌 Lưu ý"
            )

            st.text(
                str(tour["notes"])
            )


        st.markdown("---")


        # ----------------------------------------------------
        # KIỂM TRA SỐ CHỖ
        # ----------------------------------------------------

        booked_df = read_query(
            """
            SELECT
                COALESCE(
                    SUM(quantity),
                    0
                ) AS booked_people
            FROM bookings
            WHERE tour_id = :tour_id
            """,
            {
                "tour_id": tour_id
            }
        )


        booked_people = int(
            booked_df.iloc[0]["booked_people"]
        )


        max_people = int(
            tour["max_people"]
        )


        remaining = (
            max_people
            - booked_people
        )


        st.metric(
            "🪑 Số chỗ còn lại",
            f"{remaining} / {max_people}"
        )


        if remaining <= 0:

            st.error(
                "❌ Tour đã đủ số lượng khách."
            )

        else:

            quantity = st.number_input(
                "👥 Số lượng khách",
                min_value=1,
                max_value=remaining,
                value=1,
                step=1
            )


            total_price = (
                tour_price
                * quantity
            )


            st.metric(
                "💰 TỔNG TIỀN",
                f"{total_price:,.0f} VNĐ"
            )


            payment_status = st.selectbox(
                "💳 Trạng thái thanh toán",
                [
                    "Chưa thanh toán",
                    "Đã đặt cọc",
                    "Đã thanh toán"
                ]
            )


            if st.button(
                "🎫 XÁC NHẬN ĐẶT TOUR",
                use_container_width=True
            ):

                success = execute_query(
                    """
                    INSERT INTO bookings
                    (
                        created_at,
                        customer_id,
                        tour_id,
                        quantity,
                        total_price,
                        payment_status
                    )

                    VALUES
                    (
                        :created_at,
                        :customer_id,
                        :tour_id,
                        :quantity,
                        :total_price,
                        :payment_status
                    )
                    """,
                    {
                        "created_at": datetime.now(),
                        "customer_id": customer_id,
                        "tour_id": tour_id,
                        "quantity": quantity,
                        "total_price": total_price,
                        "payment_status": payment_status
                    }
                )


                if success:

                    st.success(
                        "🎉 Đặt tour thành công!"
                    )

                    st.success(
                        f"💰 Tổng tiền: "
                        f"{total_price:,.0f} VNĐ"
                    )

                    st.balloons()

                    st.rerun()


# ============================================================
# 19. HÓA ĐƠN
# ============================================================

elif page == "🧾 Hóa đơn":

    st.title(
        "🧾 QUẢN LÝ HÓA ĐƠN"
    )


    df_history = load_booking_history()


    if df_history.empty:

        st.info(
            "📭 Hệ thống chưa có booking nào."
        )


    else:

        df_history["Tổng tiền"] = pd.to_numeric(
            df_history["Tổng tiền"],
            errors="coerce"
        ).fillna(0)


        total_revenue = (
            df_history["Tổng tiền"].sum()
        )


        total_people = (
            df_history["Số khách"].sum()
        )


        paid_revenue = (
            df_history[
                df_history["Trạng thái"]
                == "Đã thanh toán"
            ]["Tổng tiền"].sum()
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "💰 Tổng giá trị booking",
                f"{total_revenue:,.0f} VNĐ"
            )


        with col2:

            st.metric(
                "👥 Tổng số khách",
                int(total_people)
            )


        with col3:

            st.metric(
                "✅ Đã thanh toán",
                f"{paid_revenue:,.0f} VNĐ"
            )


        st.markdown("---")


        st.subheader(
            "📋 Danh sách booking"
        )


        st.dataframe(
            df_history,
            use_container_width=True,
            hide_index=True
        )


        st.markdown("---")


        st.subheader(
            "💳 Cập nhật trạng thái thanh toán"
        )


        booking_ids = (
            df_history["ID"].tolist()
        )


        selected_booking = st.selectbox(
            "Chọn ID booking",
            booking_ids
        )


        new_status = st.selectbox(
            "Trạng thái mới",
            [
                "Chưa thanh toán",
                "Đã đặt cọc",
                "Đã thanh toán"
            ]
        )


        if st.button(
            "💾 CẬP NHẬT THANH TOÁN",
            use_container_width=True
        ):

            success = execute_query(
                """
                UPDATE bookings

                SET payment_status = :status

                WHERE id = :booking_id
                """,
                {
                    "status": new_status,
                    "booking_id": int(
                        selected_booking
                    )
                }
            )


            if success:

                st.success(
                    "✅ Cập nhật trạng thái thành công!"
                )

                st.rerun()


# ============================================================
# 20. ADMIN
# ============================================================

elif page == "🔑 Admin":

    st.title(
        "🔑 TRANG QUẢN TRỊ"
    )


    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if not st.session_state.admin_logged_in:

        with st.form(
            "admin_login"
        ):

            password = st.text_input(
                "🔐 Mật khẩu quản trị",
                type="password"
            )


            login = st.form_submit_button(
                "🔑 ĐĂNG NHẬP"
            )


            if login:

                if password == "123456":

                    st.session_state.admin_logged_in = True

                    st.success(
                        "✅ Đăng nhập thành công!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Mật khẩu không chính xác."
                    )


        st.stop()


    # --------------------------------------------------------
    # ADMIN ĐÃ ĐĂNG NHẬP
    # --------------------------------------------------------

    col1, col2 = st.columns(
        [5, 1]
    )


    with col1:

        st.success(
            "🟢 Quyền quản trị viên đã được xác thực."
        )


    with col2:

        if st.button(
            "🔒 Đăng xuất"
        ):

            st.session_state.admin_logged_in = False

            st.rerun()


    tab1, tab2, tab3 = st.tabs(
        [
            "🚌 Danh sách Tour",
            "💰 Doanh thu & Booking",
            "📊 Phân tích"
        ]
    )


    # ========================================================
    # ADMIN - TOUR
    # ========================================================

    with tab1:

        st.subheader(
            "🚌 Danh sách chương trình tour"
        )


        df_tours = read_query(
            """
            SELECT
                id,
                tour_name,
                destination,
                departure_date,
                return_date,
                duration,
                price,
                max_people,
                transport,
                hotel,
                meals,
                tour_guide,
                image_url,
                description,
                itinerary,
                included,
                excluded,
                notes
            FROM tours
            ORDER BY departure_date
            """
        )


        if df_tours.empty:

            st.info(
                "📭 Chưa có tour."
            )

        else:

            display = df_tours[
                [
                    "id",
                    "tour_name",
                    "destination",
                    "departure_date",
                    "return_date",
                    "duration",
                    "price",
                    "max_people",
                    "transport",
                    "hotel",
                    "meals",
                    "tour_guide"
                ]
            ].copy()


            display.columns = [
                "ID",
                "Tên tour",
                "Điểm đến",
                "Khởi hành",
                "Kết thúc",
                "Số ngày",
                "Giá",
                "Số khách tối đa",
                "Phương tiện",
                "Khách sạn",
                "Ăn uống",
                "HDV"
            ]


            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


            st.markdown("---")

            st.subheader(
                "📖 Xem nội dung chương trình"
            )


            for _, tour in df_tours.iterrows():

                with st.expander(
                    f"🚌 {tour['tour_name']}"
                ):

                    if pd.notna(
                        tour.get("description")
                    ):

                        st.markdown(
                            "### 📖 Giới thiệu"
                        )

                        st.write(
                            tour["description"]
                        )


                    if pd.notna(
                        tour.get("itinerary")
                    ):

                        st.markdown(
                            "### 🗓️ Lịch trình"
                        )

                        st.text(
                            str(tour["itinerary"])
                        )


                    if pd.notna(
                        tour.get("included")
                    ):

                        st.markdown(
                            "### ✅ Bao gồm"
                        )

                        st.text(
                            str(tour["included"])
                        )


                    if pd.notna(
                        tour.get("excluded")
                    ):

                        st.markdown(
                            "### ❌ Không bao gồm"
                        )

                        st.text(
                            str(tour["excluded"])
                        )


                    if pd.notna(
                        tour.get("notes")
                    ):

                        st.markdown(
                            "### 📌 Lưu ý"
                        )

                        st.text(
                            str(tour["notes"])
                        )


    # ========================================================
    # ADMIN - DOANH THU
    # ========================================================

    with tab2:

        st.subheader(
            "💰 Doanh thu & lịch sử booking"
        )


        df_history = load_booking_history()


        if df_history.empty:

            st.info(
                "📭 Chưa có booking."
            )

        else:

            df_history["Tổng tiền"] = pd.to_numeric(
                df_history["Tổng tiền"],
                errors="coerce"
            ).fillna(0)


            total_revenue = (
                df_history["Tổng tiền"].sum()
            )


            total_people = (
                df_history["Số khách"].sum()
            )


            total_bookings = len(
                df_history
            )


            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(
                    "💰 Tổng doanh thu",
                    f"{total_revenue:,.0f} VNĐ"
                )


            with col2:

                st.metric(
                    "🎫 Tổng booking",
                    total_bookings
                )


            with col3:

                st.metric(
                    "👥 Tổng khách",
                    int(total_people)
                )


            st.markdown("---")


            st.subheader(
                "📅 Doanh thu theo ngày"
            )


            df_history["Thời gian"] = pd.to_datetime(
                df_history["Thời gian"]
            )


            df_history["Ngày"] = (
                df_history["Thời gian"].dt.date
            )


            daily_revenue = (
                df_history
                .groupby("Ngày")["Tổng tiền"]
                .sum()
                .reset_index()
            )


            st.bar_chart(
                daily_revenue.set_index(
                    "Ngày"
                )["Tổng tiền"]
            )


            st.markdown("---")


            st.subheader(
                "📋 Lịch sử booking"
            )


            st.dataframe(
                df_history,
                use_container_width=True,
                hide_index=True
            )


    # ========================================================
    # ADMIN - PHÂN TÍCH
    # ========================================================

    with tab3:

        st.subheader(
            "📊 Thống kê & phân tích"
        )


        df_anal = load_booking_history()


        if df_anal.empty:

            st.info(
                "📭 Chưa có dữ liệu để phân tích."
            )

        else:

            df_anal["Tổng tiền"] = pd.to_numeric(
                df_anal["Tổng tiền"],
                errors="coerce"
            ).fillna(0)


            df_anal["Số khách"] = pd.to_numeric(
                df_anal["Số khách"],
                errors="coerce"
            ).fillna(0)


            # ------------------------------------------------
            # KHÁCH THEO TOUR
            # ------------------------------------------------

            tour_quantity = (
                df_anal
                .groupby("Tên tour")["Số khách"]
                .sum()
                .reset_index()
            )


            st.write(
                "### 🚌 Số khách theo từng tour"
            )


            st.bar_chart(
                tour_quantity.set_index(
                    "Tên tour"
                )["Số khách"]
            )


            # ------------------------------------------------
            # DOANH THU THEO TOUR
            # ------------------------------------------------

            tour_revenue = (
                df_anal
                .groupby("Tên tour")["Tổng tiền"]
                .sum()
                .reset_index()
            )


            tour_revenue.columns = [
                "Tên tour",
                "Doanh thu"
            ]


            st.write(
                "### 💰 Doanh thu theo tour"
            )


            st.bar_chart(
                tour_revenue.set_index(
                    "Tên tour"
                )["Doanh thu"]
            )


            # ------------------------------------------------
            # KHÁCH THEO ĐIỂM ĐẾN
            # ------------------------------------------------

            destination_quantity = (
                df_anal
                .groupby("Điểm đến")["Số khách"]
                .sum()
                .reset_index()
            )


            destination_quantity.columns = [
                "Điểm đến",
                "Số khách"
            ]


            st.write(
                "### 📍 Số khách theo điểm đến"
            )


            st.dataframe(
                destination_quantity,
                use_container_width=True,
                hide_index=True
            )


            # ------------------------------------------------
            # BẢNG DOANH THU
            # ------------------------------------------------

            st.write(
                "### 📊 Bảng doanh thu theo tour"
            )


            tour_revenue_display = (
                tour_revenue.copy()
            )


            tour_revenue_display["Doanh thu"] = (
                tour_revenue_display["Doanh thu"]
                .apply(
                    lambda x:
                    f"{x:,.0f} VNĐ"
                )
            )


            st.dataframe(
                tour_revenue_display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# 21. FOOTER
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "✈️ Hệ thống quản lý tour trọn gói"
)

st.sidebar.caption(
    "BVU - Quản trị dịch vụ du lịch và lữ hành"
)
