import streamlit as st
from PIL import Image
import requests
import base64
from io import BytesIO

# --- 1. Cấu hình trang web ---
st.set_page_config(
    page_title="AI Nhận Diện Bệnh Lá Cà Phê",
    page_icon="☕",
    layout="centered"
)

# --- 2. Thông số kết nối Roboflow (Kiểm tra kỹ trong mục Deploy -> Hosted API) ---
API_KEY = "VJBE8s72PByt8YgppZzb"
MODEL_ID = "caphe/8"  # Thay bằng chính xác chuỗi model_id trên Roboflow của bạn

# --- 3. Cơ sở dữ liệu kiến thức bệnh cây cà phê ---
DISEASE_DB = {
    'Coffee_Leaf_Rust': {
        'name': 'Bệnh Gỉ sắt (Coffee Leaf Rust)',
        'symptom': "**Tác nhân:** Do nấm *Hemileia vastatrix* gây ra.\n\n**Triệu chứng:** Mặt dưới lá xuất hiện các đốm tròn nhỏ màu vàng nhạt, bề mặt phủ lớp bột bào tử màu cam sậm.",
        'treatment': "* **🌿 Canh tác:** Cắt tỉa cành vô hiệu, tạo độ thông thoáng cho vườn cây.\n* **💊 Thuốc BVTV:** Phun các loại thuốc gốc Đồng hoặc hoạt chất *Hexaconazole*, *Propiconazole* khi bệnh mới chớm xuất hiện.",
        'prevention': "Ưu tiên trồng các giống cà phê có khả năng kháng bệnh gỉ sắt tốt và bón phân cân đối."
    },
    'Brown_Eye_Spot': {
        'name': 'Bệnh Đốm mắt cua (Cercospora)',
        'symptom': "**Tác nhân:** Do nấm *Cercospora coffeicola* gây ra.\n\n**Triệu chứng:** Vết bệnh trên lá có hình tròn, phần tâm màu xám trắng, bao quanh bởi viền nâu sẫm giống hình mắt cua.",
        'treatment': "* **🌿 Canh tác:** Bổ sung thêm phân hữu cơ hoai mục và cung cấp đầy đủ phân đạm.\n* **💊 Thuốc BVTV:** Phun phòng trị bằng các thuốc chứa hoạt chất *Carbendazim* hoặc *Mancozeb*.",
        'prevention': "Quản lý chế độ dinh dưỡng và che bóng hợp lý cho vườn cây ngay từ đầu mùa mưa."
    },
    'Anthracnose_Leaf': {
        'name': 'Bệnh Thán thư hại lá (Anthracnose)',
        'symptom': "**Tác nhân:** Do nấm *Colletotrichum coffeanum* gây ra.\n\n**Triệu chứng:** Trên phiến lá hình thành các đốm màu nâu sẫm có vân vòng đồng tâm, thường lan từ mép lá vào trong.",
        'treatment': "* **🌿 Canh tác:** Thu gom và tiêu hủy các cành khô, cành chết, lá rụng bị bệnh.\n* **💊 Thuốc BVTV:** Sử dụng thuốc chứa hoạt chất *Tebuconazole*, *Azoxystrobin* hoặc *Mancozeb*.",
        'prevention': "Bón bổ sung chế phẩm nấm đối kháng *Trichoderma* vào vùng rễ để tăng sức đề kháng cho cây."
    },
    'Red_Alga': {
        'name': 'Bệnh Đốm tảo đỏ (Red Alga)',
        'symptom': "**Tác nhân:** Do loài tảo ký sinh *Cephaleuros virescens* gây ra.\n\n**Triệu chứng:** Mặt trên của lá xuất hiện các đốm tròn màu đỏ cam, bề mặt hơi gồ lên như lớp nhung mịn.",
        'treatment': "* **🌿 Canh tác:** Rong tỉa cành rậm rạp, dọn sạch cỏ dại để giảm độ ẩm trong vườn.\n* **💊 Thuốc BVTV:** Phun phủ đều tán lá bằng các loại thuốc gốc Đồng như *COC 85* hoặc *Bordeaux*.",
        'prevention': "Tỉa cành tạo tán định kỳ hàng năm giúp ánh nắng xuyên qua tán lá."
    },
    'healthy': {
        'name': 'Lá Cà Phê Khỏe Mạnh (Healthy)',
        'symptom': "### 🎉 Cây cà phê đang phát triển tốt!\nPhiến lá xanh bóng mượt, dày dặn, không ghi nhận dấu hiệu của nấm bệnh hay tảo ký sinh.",
        'treatment': "* **💧 Tưới nước:** Duy trì độ ẩm đất phù hợp, đặc biệt trong giai đoạn phân hóa mầm hoa.\n* **🧪 Dinh dưỡng:** Bón phân NPK cân đối theo từng giai đoạn sinh trưởng.",
        'prevention': "Thường xuyên thăm vườn, kiểm tra mặt dưới lá và các chùm quả non để phòng ngừa rệp sáp."
    }
}

# --- 4. Hàm gửi ảnh và nhận diện từ Roboflow ---
def phan_tich_anh_roboflow(image_pil):
    clean_model_id = MODEL_ID.strip("/")
    # Sử dụng máy chủ Serverless API mới nhất của Roboflow
    endpoint = f"https://serverless.roboflow.com/{clean_model_id}"
    
    try:
        img_resized = image_pil.copy()
        img_resized.thumbnail((800, 800))

        buffer = BytesIO()
        img_resized.save(buffer, format="JPEG", quality=90)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        query_params = {"api_key": API_KEY}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            url=endpoint,
            params=query_params,
            data=img_base64,
            headers=headers,
            timeout=15
        )

        if response.status_code == 200:
            return {"status": "success", "data": response.json(), "url_used": endpoint}
        else:
            return {
                "status": "error", 
                "code": response.status_code,
                "message": response.text[:300], # Rút gọn thông báo lỗi cho dễ đọc
                "url_used": endpoint
            }

    except Exception as e:
        return {"status": "error", "code": "Exception", "message": str(e), "url_used": endpoint}

# --- 5. Giao diện người dùng (UI) ---
st.markdown("""
<style>
    .stApp { background-color: #fcfaf7; }
    h1 { color: #4E342E; text-align: center; font-weight: bold; }
    .footer { text-align: center; margin-top: 50px; color: #777; font-size: 0.9em; border-top: 1px solid #ddd; padding-top: 15px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>☕ HỆ THỐNG AI CHẨN ĐOÁN BỆNH LÁ CÀ PHÊ 🍃</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📁 Tải ảnh từ thiết bị", "📸 Chụp ảnh bằng Camera"])

selected_file = None

with tab1:
    uploaded_file = st.file_uploader("Chọn tệp ảnh lá cà phê (JPG, PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        selected_file = uploaded_file

with tab2:
    st.info("💡 Đưa camera lại gần vùng lá có vết bệnh và giữ chắc tay để ảnh sắc nét.")
    camera_file = st.camera_input("Chụp trực tiếp lá cà phê")
    if camera_file:
        selected_file = camera_file

# --- 6. Xử lý khi có ảnh đầu vào ---
if selected_file is not None:
    image = Image.open(selected_file).convert("RGB")
    st.image(image, caption="Ảnh mẫu đang phân tích", use_container_width=True)

    with st.spinner("⏳ Đang kết nối máy chủ AI Roboflow để phân tích..."):
        result = phan_tich_anh_roboflow(image)

        if result["status"] == "error":
            st.error(f"❌ Lỗi kết nối (Mã {result.get('code')}): Không tìm thấy mô hình `{MODEL_ID}`")
            st.info(f"👉 Bạn hãy kiểm tra lại mục **Deploy -> Hosted API** trên Roboflow xem tên `model_id` có đúng là `{MODEL_ID}` không nhé.")
            st.caption(f"Địa chỉ đã gọi: `{result.get('url_used')}`")
        else:
            raw_json = result["data"]
            top_label = None
            confidence = 0.0

            # Đọc kết quả từ JSON (hỗ trợ cả Classification và Object Detection)
            if "top" in raw_json:
                top_label = raw_json["top"]
                confidence = raw_json.get("confidence", 0.0)
            elif "predictions" in raw_json:
                preds = raw_json["predictions"]
                if isinstance(preds, dict) and len(preds) > 0:
                    top_label = max(preds, key=lambda k: preds[k].get("confidence", 0) if isinstance(preds[k], dict) else preds[k])
                    val = preds[top_label]
                    confidence = val.get("confidence", 0.0) if isinstance(val, dict) else val
                elif isinstance(preds, list) and len(preds) > 0:
                    best_pred = max(preds, key=lambda x: x.get("confidence", 0))
                    top_label = best_pred.get("class")
                    confidence = best_pred.get("confidence", 0.0)

            if confidence <= 1.0:
                confidence *= 100

            if top_label:
                disease_info = DISEASE_DB.get(top_label)
                if disease_info:
                    st.success(f"**Kết quả chẩn đoán:** {disease_info['name']} *(Độ tin cậy: {confidence:.1f}%)*")
                    
                    if confidence < 60.0:
                        st.warning("⚠️ Độ tin cậy thấp. Khuyến nghị chụp lại ảnh rõ nét và đủ ánh sáng hơn.")

                    with st.expander("📝 Triệu chứng & Tác nhân gây bệnh", expanded=True):
                        st.markdown(disease_info['symptom'])
                    with st.expander("✅ Biện pháp xử lý & Chữa trị", expanded=True):
                        st.markdown(disease_info['treatment'])
                    with st.expander("🛡️ Cách phòng ngừa tái phát"):
                        st.markdown(disease_info['prevention'])
                else:
                    st.warning(f"**Nhãn AI trả về:** `{top_label}` *(Độ tin cậy: {confidence:.1f}%)*")
                    st.info("Nhãn này chưa được cập nhật thông tin chi tiết trong từ điển `DISEASE_DB`.")

                with st.expander("🛠️ Dữ liệu kỹ thuật (JSON)"):
                    st.write(f"**Endpoint:** `{result.get('url_used')}`")
                    st.json(raw_json)
            else:
                st.warning("Máy chủ phản hồi thành công nhưng không phát hiện thấy dấu hiệu bệnh nào trên ảnh.")
                with st.expander("🛠️ Dữ liệu kỹ thuật (JSON)"):
                    st.json(raw_json)

st.markdown("<div class='footer'>Dự án Nghiên cứu Khoa học Kỹ thuật - Nhóm Nghiên cứu AI Trường THPT Hoàng Hoa Thám</div>", unsafe_allow_html=True)
