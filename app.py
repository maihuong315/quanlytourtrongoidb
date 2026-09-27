```python
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
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",
    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "database": "defaultdb"
}


# ============================================================
# 3. DATABASE URL
# ============================================================

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB["user"],
    password=DB["password"],
    host=DB["host"],
    port=DB["port"],
    database=DB["database"]
)


# ============================================================
# 4. TẠO DATABASE ENGINE
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
# 5. KIỂM TRA KẾT NỐI DATABASE
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
# 6. HIỂN THỊ TRẠNG THÁI DATABASE
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


# ============================================================
# 7. TẠO CÁC BẢNG DATABASE
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


if db_connected:

    try:

        init_db()

    except Exception as e:

        st.error(
            "❌ Không thể tạo bảng Database."
        )

        st.code(str(e))

        st.stop()

else:

    st.stop()


# ============================================================
# 8. HÀM ĐỌC DATABASE
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
# 9. HÀM GHI DATABASE
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
# 10. LỊCH SỬ BOOKING
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
# 11. SESSION STATE
# ============================================================

if "admin_logged_in" not in st.session_state:

    st.session_state.admin_logged_in = False


# ============================================================
# 12. SIDEBAR
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
# 13. TRANG TỔNG QUAN
# ============================================================

if page == "🏠 Tổng quan":

    st.title(
        "✈️ HỆ THỐNG QUẢN LÝ TOUR TRỌN GÓI"
    )

    st.caption(
        "Quản lý tour - khách hàng - booking - thanh toán - doanh thu"
    )

    st.success(
        "🟢 MySQL: ĐÃ KẾT NỐI"
    )

    st.markdown("---")


    df_tours = read_query(
        "SELECT * FROM tours"
    )

    df_customers = read_query(
        "SELECT * FROM customers"
    )

    df_bookings = read_query(
        "SELECT * FROM bookings"
    )


    # --------------------------------------------------------
    # KPI
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

    st.subheader(
        "🚌 Các tour đang kinh doanh"
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


    else:

        st.info(
            "Chưa có tour nào. "
            "Hãy vào Quản lý Tour để tạo tour."
        )


# ============================================================
# 14. QUẢN LÝ TOUR
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


    # --------------------------------------------------------
    # TẠO TOUR
    # --------------------------------------------------------

    with tab1:

        st.subheader(
            "➕ Tạo chương trình tour mới"
        )


        with st.form("create_tour_form"):

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


            description = st.text_area(
                "📝 Nội dung / lịch trình tour",
                placeholder="Mô tả lịch trình và dịch vụ..."
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
                            "description": description,
                            "created_at": datetime.now()
                        }
                    )


                    if success:

                        st.success(
                            "🎉 Tạo tour thành công!"
                        )

                        st.rerun()


    # --------------------------------------------------------
    # DANH SÁCH TOUR
    # --------------------------------------------------------

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
                description
            FROM tours
            ORDER BY departure_date ASC
            """
        )


        if not df.empty:

            display = df.copy()


            display.columns = [
                "ID",
                "Tên tour",
                "Điểm đến",
                "Khởi hành",
                "Kết thúc",
                "Số ngày",
                "Giá tour",
                "Số khách tối đa",
                "Phương tiện",
                "Khách sạn",
                "Ăn uống",
                "HDV",
                "Mô tả"
            ]


            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


        else:

            st.info(
                "Chưa có tour."
            )


# ============================================================
# 15. QUẢN LÝ KHÁCH HÀNG
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


    # --------------------------------------------------------
    # THÊM KHÁCH HÀNG
    # --------------------------------------------------------

    with tab1:

        with st.form("customer_form"):

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


    # --------------------------------------------------------
    # DANH SÁCH KHÁCH HÀNG
    # --------------------------------------------------------

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


        if not df_customers.empty:

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


        else:

            st.info(
                "Chưa có khách hàng."
            )


# ============================================================
# 16. ĐẶT TOUR
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
            max_people
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


        st.markdown("---")


        # --------------------------------------------------------
        # KIỂM TRA SỐ CHỖ
        # --------------------------------------------------------

        booked_df = read_query(
            """
            SELECT
                COALESCE(SUM(quantity), 0) AS booked_people
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


        remaining = max_people - booked_people


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
                tour_price * quantity
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
# 17. HÓA ĐƠN
# ============================================================

elif page == "🧾 Hóa đơn":

    st.title(
        "🧾 QUẢN LÝ HÓA ĐƠN"
    )


    df_history = load_booking_history()


    if df_history.empty:

        st.info(
            "Hệ thống chưa có booking nào."
        )


    else:

        df_history["Tổng tiền"] = pd.to_numeric(
            df_history["Tổng tiền"],
            errors="coerce"
        ).fillna(0)


        total_revenue = df_history[
            "Tổng tiền"
        ].sum()


        total_people = df_history[
            "Số khách"
        ].sum()


        paid_revenue = df_history[
            df_history["Trạng thái"] == "Đã thanh toán"
        ]["Tổng tiền"].sum()


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


        booking_ids = df_history[
            "ID"
        ].tolist()


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
                    "booking_id": int(selected_booking)
                }
            )


            if success:

                st.success(
                    "✅ Cập nhật trạng thái thành công!"
                )

                st.rerun()


# ============================================================
# 18. ADMIN
# ============================================================

elif page == "🔑 Admin":

    st.title(
        "🔑 TRANG QUẢN TRỊ"
    )


    # --------------------------------------------------------
    # ĐĂNG NHẬP
    # --------------------------------------------------------

    if not st.session_state.admin_logged_in:

        with st.form("admin_login"):

            password = st.text_input(
                "🔐 Mật khẩu quản trị",
                type="password"
            )


            login = st.form_submit_button(
                "🔑 ĐĂNG NHẬP"
            )


            if login:

                # Mật khẩu demo cho bài tập
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


        st.info(
            "Đây là mật khẩu demo của bài tập."
        )

        st.stop()


    # --------------------------------------------------------
    # ĐÃ ĐĂNG NHẬP
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


    # --------------------------------------------------------
    # ADMIN TABS
    # --------------------------------------------------------

    tab1, tab2, tab3 = st.tabs(
        [
            "🚌 Danh sách Tour",
            "💰 Doanh thu & Booking",
            "📊 Phân tích"
        ]
    )


    # ========================================================
    # TAB 1
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
                tour_guide
            FROM tours
            ORDER BY departure_date
            """
        )


        if not df_tours.empty:

            df_tours.columns = [
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
                df_tours,
                use_container_width=True,
                hide_index=True
            )


        else:

            st.info(
                "Chưa có tour."
            )


    # ========================================================
    # TAB 2
    # ========================================================

    with tab2:

        st.subheader(
            "💰 Doanh thu & lịch sử booking"
        )


        df_history = load_booking_history()


        if df_history.empty:

            st.info(
                "Chưa có booking."
            )


        else:

            df_history["Tổng tiền"] = pd.to_numeric(
                df_history["Tổng tiền"],
                errors="coerce"
            ).fillna(0)


            total_revenue = df_history[
                "Tổng tiền"
            ].sum()


            total_people = df_history[
                "Số khách"
            ].sum()


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


            st.subheader(
                "📋 Lịch sử booking"
            )


            st.dataframe(
                df_history,
                use_container_width=True,
                hide_index=True
            )


    # ========================================================
    # TAB 3 - PHÂN TÍCH
    # ========================================================

    with tab3:

        st.subheader(
            "📊 Thống kê & phân tích tour"
        )


        df_anal = load_booking_history()


        if df_anal.empty:

            st.info(
                "Chưa có dữ liệu booking để phân tích."
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
            # THỐNG KÊ THEO TOUR
            # ------------------------------------------------

            tour_quantity = (
                df_anal
                .groupby("Tên tour")["Số khách"]
                .sum()
                .reset_index()
            )


            tour_quantity.columns = [
                "Tên tour",
                "Số khách"
            ]


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
            # ĐIỂM ĐẾN
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
                    lambda x: f"{x:,.0f} VNĐ"
                )
            )


            st.dataframe(
                tour_revenue_display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# 19. FOOTER
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "✈️ Hệ thống quản lý tour trọn gói"
)

st.sidebar.caption(
    "BVU - Quản trị dịch vụ du lịch và lữ hành"
)
```
