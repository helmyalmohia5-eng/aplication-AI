import streamlit as st
from google import genai
from PIL import Image
from gtts import gTTS
from pypdf import PdfReader
import io

# =============================================================
# 1. تهيئة الصفحة والـ API
# =============================================================
st.set_page_config(
    page_title="AuraStudy AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# جلب المفتاح تلقائياً من secrets أو القائمة الجانبية
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("🔑 أدخل مفتاح Gemini API:", type="password")

if not api_key:
    st.info("💡 يرجى إضافة مفتاح GEMINI_API_KEY في ملف secrets.toml أو القائمة الجانبية لتفعيل النظام.")
    st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"خطأ في تهيئة عميل Gemini: {e}")
    st.stop()

# =============================================================
# 2. النظام الذكي لاكتشاف واختيار النموذج المتاح تلقائياً (منع 404)
# =============================================================
@st.cache_resource
def get_best_model(_client):
    candidates = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    # تجربة النماذج بالترتيب لاكتشاف أيهما يعمل على حسابك
    for model_name in candidates:
        try:
            _client.models.generate_content(
                model=model_name,
                contents="test"
            )
            return model_name
        except Exception:
            continue
            
    # محاولة فحص قائمة النماذج في الحساب مباشرة
    try:
        models_list = list(_client.models.list())
        for m in models_list:
            m_name = m.name.replace("models/", "")
            if "flash" in m_name or "pro" in m_name:
                try:
                    _client.models.generate_content(model=m_name, contents="test")
                    return m_name
                except Exception:
                    continue
    except Exception:
        pass
        
    return "gemini-1.5-flash"

ACTIVE_MODEL = get_best_model(client)

# =============================================================
# 3. تهيئة الـ session_state لحفظ الحالة ومنع أخطاء NoneType
# =============================================================
if "pdf_text" not in st.session_state or st.session_state["pdf_text"] is None:
    st.session_state["pdf_text"] = ""

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        extracted_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"
        return extracted_text
    except Exception as e:
        st.error(f"خطأ في قراءة ملف الـ PDF: {e}")
        return ""

def text_to_speech(text):
    try:
        clean_text = text.replace("*", "").replace("#", "")[:500]
        tts = gTTS(text=clean_text, lang='ar')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception:
        return None

# =============================================================
# 4. القائمة الجانبية (Sidebar)
# =============================================================
with st.sidebar:
    st.title("🎓 AuraStudy AI")
    st.success(f"🟢 النموذج النشط: {ACTIVE_MODEL}")
    st.markdown("---")
    
    st.subheader("📄 إدارة المستند (PDF)")
    uploaded_pdf = st.file_uploader("اختر ملف PDF للتحليل:", type=["pdf"])
    
    if uploaded_pdf:
        if st.button("📖 قراءة ومعالجة المستند"):
            with st.spinner("جاري استخراج النصوص من المستند..."):
                text = extract_text_from_pdf(uploaded_pdf)
                if text.strip():
                    st.session_state["pdf_text"] = text
                    st.success(f"تمت قراءة المستند بنجاح! ({len(text)} حرف)")
                else:
                    st.warning("تعذر استخراج نص واضح من هذا الملف.")
    
    if st.session_state["pdf_text"]:
        st.info("📌 يوجد مستند معالج حالياً في الذاكرة.")
        if st.button("🗑️ مسح المستند من الذاكرة"):
            st.session_state["pdf_text"] = ""
            st.rerun()

    st.markdown("---")
    st.caption("تطوير: مهندس حلمي والمساعد الذكي")

# =============================================================
# 5. التبويبات الـ 6 الشاملة
# =============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 الدردشة والمساعد الأكاديمي", 
    "📷 تحليل الصور والمسائل", 
    "🎴 بطاقات المراجعة", 
    "🗺️ خريطة المفاهيم", 
    "🌙 ليلة الامتحان", 
    "📝 الاختبار التفاعلي"
])

# -------------------------------------------------------------
# التبويب 1: الدردشة والمساعد الأكاديمي (عام أو من المستند)
# -------------------------------------------------------------
with tab1:
    col_mode, col_style = st.columns(2)
    with col_mode:
        mode = st.radio(
            "نطاق الإجابة:",
            ["🌐 المعرفة العامة الشاملة (ذكاء اصطناعي)", "🎯 الإجابة من ملف الـ PDF فقط"],
            horizontal=False
        )
    with col_style:
        style = st.selectbox(
            "أسلوب الإجابة والشرح:",
            [
                "أكاديمي دقيق 🎯",
                "تبسيط المفاهيم (Feynman) 💡",
                "تطبيقات وأمثلة عملية 💻"
            ]
        )

    st.markdown("---")

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    user_input = st.chat_input("اسأل عن أي موضوع، قانون، أو مسألة...")

    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        pdf_content = st.session_state.get("pdf_text", "") or ""

        if "PDF" in mode:
            if not pdf_content.strip():
                st.warning("⚠️ اخترت الإجابة من المستند ولكن لم تقم برفع وقراءة ملف PDF بعد! يرجى رفع الملف أو التبديل للنطاق العام.")
                st.stop()
            full_prompt = f"الأسلوب المطلوب: {style}\n\n[استناداً للنص التالي من المستند فقط]\nالنص:\n{pdf_content}\n\nسؤال المستخدم: {user_input}"
        else:
            if pdf_content.strip():
                full_prompt = f"الأسلوب المطلوب: {style}\n\n[سياق إضافي من المستند المرفق إن لزم]:\n{pdf_content}\n\nسؤال المستخدم: {user_input}"
            else:
                full_prompt = f"الأسلوب المطلوب: {style}\n\nسؤال المستخدم: {user_input}"

        with st.chat_message("assistant"):
            with st.spinner("جاري التفكير وتحليل السؤال..."):
                try:
                    res = client.models.generate_content(
                        model=ACTIVE_MODEL,
                        contents=full_prompt
                    )
                    response_text = res.text
                    st.markdown(response_text)
                    
                    audio_fp = text_to_speech(response_text)
                    if audio_fp:
                        st.audio(audio_fp, format="audio/mp3")
                    
                    st.session_state["chat_history"].append({
                        "role": "assistant", 
                        "content": response_text,
                        "audio": audio_fp
                    })
                except Exception as e:
                    st.error(f"حدث خطأ أثناء التوليد: {e}")

# -------------------------------------------------------------
# التبويب 2: تحليل الصور والمسائل
# -------------------------------------------------------------
with tab2:
    st.header("📷 تحليل الصور ورسم الحلول الخطوة بخطوة")
    
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        img_file = st.file_uploader("رفع صورة (مسألة/رسم بياني/جدول):", type=["jpg", "jpeg", "png"], key="vision_uploader")
    with col_img2:
        cam_file = st.camera_input("أو التقط صورة بالكاميرا مباشرة", key="vision_camera")

    active_image = img_file or cam_file

    if active_image:
        image_obj = Image.open(active_image)
        st.image(image_obj, caption="📷 الصورة المدخلة", use_container_width=True)
        
        image_prompt = st.text_area(
            "✍️ ما الذي تريد استخراجه أو مناقشته حول هذه الصورة؟",
            value="على ماذا تدل هذه الصورة؟ حل المسألة إن وجدت واشرح التفاصيل بدقة.",
            key="img_prompt_input"
        )
        
        if st.button("🔍 تحليل الصورة ورسم الحل", key="analyze_btn"):
            with st.spinner("جاري معالجة الصورة عبر الذكاء الاصطناعي..."):
                try:
                    res = client.models.generate_content(
                        model=ACTIVE_MODEL,
                        contents=[image_obj, image_prompt]
                    )
                    st.success("تم التحليل بنجاح!")
                    st.markdown(res.text)
                    
                    img_audio = text_to_speech(res.text)
                    if img_audio:
                        st.audio(img_audio, format="audio/mp3")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء تحليل الصورة: {e}")

# -------------------------------------------------------------
# التبويب 3: بطاقات المراجعة (Flashcards)
# -------------------------------------------------------------
with tab3:
    st.header("🎴 بطاقات المراجعة الذكية")
    topic_input = st.text_input("أدخل الموضوع أو حدد الفصل المراد توليد بطاقات له:", placeholder="مثال: خوارزميات التعلم العميق")
    
    if st.button("⚡ توليد بطاقات المراجعة"):
        pdf_content = st.session_state.get("pdf_text", "") or ""
        context_for_cards = f"اعتماداً على هذا المستند:\n{pdf_content}\n\n" if pdf_content.strip() else ""
        cards_prompt = f"{context_for_cards}قم بإنشاء 5 بطاقات مراجعة ذكية حول: {topic_input if topic_input else 'الموضوع الرئيسي'}. اكتب كل بطاقة بصيغة (سؤال: ... / الإجابة: ...)."
        
        with st.spinner("جاري إنشاء البطاقات..."):
            try:
                res = client.models.generate_content(model=ACTIVE_MODEL, contents=cards_prompt)
                st.markdown(res.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

# -------------------------------------------------------------
# التبويب 4: خريطة المفاهيم (Mind Map)
# -------------------------------------------------------------
with tab4:
    st.header("🗺️ خريطة المفاهيم الذهنية")
    if st.button("🌳 رسم خريطة المفاهيم للمستند الحالي"):
        pdf_content = st.session_state.get("pdf_text", "") or ""
        if pdf_content.strip():
            prompt = f"قم بتحويل النص التالي إلى خريطة مفاهيم شجرية متفرعة ومنظمة باستخدام النقاط:\n{pdf_content}"
        else:
            prompt = "أنشئ خريطة مفاهيم شجرية متفرعة ومنظمة لأساسيات الذكاء الاصطناعي وتعلم الآلة."
        
        with st.spinner("جاري بناء الخريطة..."):
            try:
                res = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
                st.markdown(res.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

# -------------------------------------------------------------
# التبويب 5: ورقة ليلة الامتحان (Cheat Sheet)
# -------------------------------------------------------------
with tab5:
    st.header("🌙 ملخص ليلة الامتحان (Cheat Sheet)")
    if st.button("📑 توليد الملخص الشامل"):
        pdf_content = st.session_state.get("pdf_text", "") or ""
        if pdf_content.strip():
            prompt = f"استخرج أهم القوانين والتعاريف والمعادلات والنقاط الحرجة من النص التالي ليكون ملخصاً مكثفاً لليلة الامتحان:\n{pdf_content}"
        else:
            prompt = "اكتب ملخصاً مكثفاً لليلة الامتحان يغطي أهم القوانين والمفاهيم في الذكاء الاصطناعي."
        
        with st.spinner("جاري تلخيص الزبدة..."):
            try:
                res = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
                st.markdown(res.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

# -------------------------------------------------------------
# التبويب 6: الاختبار التفاعلي (Quiz)
# -------------------------------------------------------------
with tab6:
    st.header("📝 اختبار تفاعلي لتقييم الفهم")
    if st.button("⚙️ توليد اختبار تفاعلي"):
        pdf_content = st.session_state.get("pdf_text", "") or ""
        if pdf_content.strip():
            prompt = f"بناءً على النص التالي، قم بإنشاء 3 أسئلة اختيارات متعددة (MCQ) مع وضع الأجوبة والتفسير في النهاية:\n{pdf_content}"
        else:
            prompt = "قم بإنشاء 3 أسئلة اختيارات متعددة (MCQ) في الذكاء الاصطناعي مع توضيح الإجابات الصحيحة والتفسير."
        
        with st.spinner("جاري إعداد الأسئلة والاختبار..."):
            try:
                res = client.models.generate_content(model=ACTIVE_MODEL, contents=prompt)
                st.markdown(res.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")



#streamlit run app.py