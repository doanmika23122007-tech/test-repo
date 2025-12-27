import streamlit as st
import pandas as pd
import random

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Flashcard Tiếng Trung Pro", page_icon="🇨🇳", layout="centered")

st.markdown("""
    <style>
    /* Nền và màu chữ chủ đạo */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* Card chứa câu hỏi */
    .question-card { 
        background: linear-gradient(145deg, #1e293b, #0f172a); 
        padding: 40px 20px; 
        border-radius: 24px; 
        border: 2px solid #38bdf8; 
        text-align: center; 
        margin-bottom: 30px;
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.2);
    }
    
    /* Input box to và căn giữa */
    .stTextInput input { 
        text-align: center; 
        font-size: 1.5rem !important; 
        border-radius: 12px !important; 
        border: 2px solid #475569;
        color: #333 !important; /* Màu chữ khi gõ */
        background-color: #f8fafc !important;
    }
    
    /* Thông báo kết quả */
    .correct-msg { 
        color: #dcfce7; background: #14532d; 
        padding: 20px; border-radius: 12px; 
        text-align: center; border: 1px solid #4ade80;
        animation: fadeIn 0.5s;
    }
    .wrong-msg { 
        color: #fee2e2; background: #7f1d1d; 
        padding: 20px; border-radius: 12px; 
        text-align: center; border: 1px solid #f87171;
        animation: fadeIn 0.5s;
    }
    
    /* Hiển thị Pinyin/Ghi chú */
    .note-text {
        font-size: 1.2rem;
        color: #fbbf24; /* Màu vàng amber */
        font-style: italic;
        margin-top: 5px;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
if 'app_state' not in st.session_state:
    st.session_state.update({
        'app_state': 'SETUP', 
        'quiz_data': [], 
        'idx': 0, 
        'score': 0, 
        'answered': False, 
        'res_status': None, 
        'font_size': 60,
        'wrong_answer_text': '' # Lưu đáp án đúng để hiển thị khi sai
    })

def reset_game():
    st.session_state.update({'app_state': 'SETUP', 'idx': 0, 'score': 0, 'answered': False})

# ==========================================
# MÀN HÌNH 1: THIẾT LẬP (SETUP)
# ==========================================
if st.session_state.app_state == 'SETUP':
    st.title("🇨🇳 Luyện Từ Vựng Tiếng Trung")
    st.markdown("Load file CSV của bạn vào đây để bắt đầu học nhé!")
    
    file = st.file_uploader("Tải file CSV (UTF-8) lên:", type=['csv'])
    
    if file:
        try:
            # Đọc file với header=0 vì file của bạn có tiêu đề
            df = pd.read_csv(file, encoding='utf-8').fillna("").astype(str)
            
            # Làm sạch tên cột (xóa khoảng trắng thừa nếu có)
            df.columns = df.columns.str.strip()
            
            st.success(f"✅ Đã đọc thành công {len(df)} từ vựng!")
            
            # --- TỰ ĐỘNG PHÁT HIỆN CỘT CHO FILE CỦA BẠN ---
            cols = list(df.columns)
            
            # Tìm vị trí mặc định dựa trên file bạn cung cấp
            # File của bạn: [STT, 1000 từ vựng..., Phiên âm, Dịch nghĩa]
            # Index tương ứng: 0, 1, 2, 3
            
            idx_q = 1 if len(cols) > 1 else 0 # Mặc định lấy cột 1 (Tiếng Trung)
            idx_a = 3 if len(cols) > 3 else (1 if len(cols)>1 else 0) # Mặc định lấy cột 3 (Dịch nghĩa)
            idx_n = 2 if len(cols) > 2 else 0 # Mặc định lấy cột 2 (Phiên âm)

            with st.expander("⚙️ Cấu hình cột (Đã tự động chọn cho bạn)", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    c_q = st.selectbox("Cột Câu Hỏi (Ngoại ngữ):", cols, index=idx_q)
                    c_a = st.selectbox("Cột Đáp Án (Tiếng Việt):", cols, index=idx_a)
                with c2:
                    c_n = st.selectbox("Cột Gợi ý/Phiên âm (Pinyin):", cols, index=idx_n)
                    mode = st.radio("Chế độ học:", ["Nhìn Trung -> Gõ Việt", "Nhìn Việt -> Gõ Trung"])

            # Cài đặt nâng cao
            c3, c4 = st.columns(2)
            with c3:
                f_size = st.slider("Cỡ chữ câu hỏi (px):", 30, 100, 70)
            with c4:
                limit = st.number_input("Số câu muốn học:", 1, len(df), min(50, len(df)))

            if st.button("🚀 BẮT ĐẦU HỌC NGAY", type="primary", use_container_width=True):
                # Chuẩn bị dữ liệu: [Câu hỏi, Đáp án, Ghi chú]
                if mode == "Nhìn Trung -> Gõ Việt":
                    # Data: [Trung, Việt, Pinyin]
                    final_data = df[[c_q, c_a, c_n]].values.tolist()
                else:
                    # Data: [Việt, Trung, Pinyin] - Chú ý Pinyin vẫn là Note
                    final_data = df[[c_a, c_q, c_n]].values.tolist()
                
                random.shuffle(final_data)
                
                st.session_state.update({
                    'quiz_data': final_data[:limit],
                    'font_size': f_size,
                    'app_state': 'PLAYING',
                    'idx': 0, 'score': 0, 'answered': False
                })
                st.rerun()
                
        except Exception as e:
            st.error(f"⚠️ Lỗi đọc file: {e}")
            st.info("Mẹo: Hãy chắc chắn file là CSV UTF-8. Nếu dùng Excel, hãy chọn 'Save As' -> 'CSV UTF-8'.")

# ==========================================
# MÀN HÌNH 2: HỌC TẬP (PLAYING)
# ==========================================
elif st.session_state.app_state == 'PLAYING':
    curr_idx = st.session_state.idx
    data = st.session_state.quiz_data
    total = len(data)
    
    # Nút quay về
    if st.sidebar.button("← Chọn file khác"):
        reset_game()
        st.rerun()

    if curr_idx < total:
        q_text, a_text, note_text = data[curr_idx]
        
        # Thanh tiến độ
        st.progress((curr_idx)/total, text=f"Tiến độ: {curr_idx}/{total}")
        st.caption(f"Điểm số: {st.session_state.score} ⭐")
        
        # --- HIỂN THỊ CÂU HỎI ---
        size = st.session_state.font_size
        st.markdown(f"""
            <div class="question-card">
                <div style="color: #94a3b8; font-size: 0.9rem; letter-spacing: 2px;">CÂU HỎI</div>
                <div style="font-size: {size}px; font-weight: bold; color: #38bdf8; margin-top: 10px; line-height: 1.2;">
                    {q_text}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- FORM TRẢ LỜI ---
        # Chỉ hiện form nếu chưa trả lời
        if not st.session_state.answered:
            with st.form(key=f"quiz_form_{curr_idx}", clear_on_submit=False):
                u_input = st.text_input("Nhập câu trả lời:", placeholder="Gõ đáp án và nhấn Enter...").strip()
                
                c1, c2 = st.columns(2)
                with c1:
                    submit = st.form_submit_button("Kiểm tra 🔍", type="primary", use_container_width=True)
                with c2:
                    give_up = st.form_submit_button("🫣 Xem đáp án", use_container_width=True)
                
                if submit and u_input:
                    st.session_state.answered = True
                    # So sánh linh hoạt (bỏ viết hoa thường, bỏ khoảng trắng thừa)
                    if u_input.lower().strip() == a_text.lower().strip():
                        st.session_state.res_status = 'RIGHT'
                        st.session_state.score += 1
                    else:
                        st.session_state.res_status = 'WRONG'
                    st.rerun()
                
                if give_up:
                    st.session_state.answered = True
                    st.session_state.res_status = 'GIVE_UP'
                    st.rerun()

        # --- HIỂN THỊ KẾT QUẢ SAU KHI TRẢ LỜI ---
        else:
            status = st.session_state.res_status
            
            if status == 'RIGHT':
                st.markdown(f"""
                <div class='correct-msg'>
                    <div style="font-size: 1.5rem;">🎉 CHÍNH XÁC!</div>
                    <div>{a_text}</div>
                    <div class="note-text">{note_text}</div>
                </div>
                """, unsafe_allow_html=True)
            elif status == 'WRONG':
                st.markdown(f"""
                <div class='wrong-msg'>
                    <div style="font-size: 1.5rem;">❌ SAI RỒI!</div>
                    <div>Đáp án đúng là: <b>{a_text}</b></div>
                    <div class="note-text">{note_text}</div>
                </div>
                """, unsafe_allow_html=True)
            else: # GIVE_UP
                 st.markdown(f"""
                <div class='wrong-msg' style='background: #451a03; border-color: #f59e0b; color: #fef3c7;'>
                    <div style="font-size: 1.2rem;">💡 ĐÁP ÁN LÀ:</div>
                    <div style="font-size: 1.5rem; font-weight: bold;">{a_text}</div>
                    <div class="note-text">{note_text}</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("") # Spacer
            if st.button("Câu tiếp theo ➡️", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.rerun()

    else:
        # ==========================================
        # MÀN HÌNH TỔNG KẾT (FINISH)
        # ==========================================
        st.session_state.app_state = 'FINISH'
        st.rerun()

elif st.session_state.app_state == 'FINISH':
    st.balloons()
    score = st.session_state.score
    total = len(st.session_state.quiz_data)
    
    st.markdown(f"""
        <div style="text-align: center; padding: 40px;">
            <h1>🏆 HOÀN THÀNH BUỔI HỌC</h1>
            <h2 style="color: #38bdf8; font-size: 3rem;">{score} / {total}</h2>
            <p>Bạn đã làm rất tốt!</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Học lại bộ này", use_container_width=True):
            st.session_state.idx = 0
            st.session_state.score = 0
            st.session_state.app_state = 'PLAYING'
            st.rerun()
    with col2:
        if st.button("📂 Tải file mới", use_container_width=True):
            reset_game()
            st.rerun()