
import streamlit as st
from brain import process_pdf, ask_question
import os
import hashlib

# إعداد الصفحة
st.set_page_config(page_title="مساعد الـ PDF الذكي", page_icon="📚", layout="wide")

st.title("🤖 اسأل ملفاتك (نسخة Groq المجانية)")

# --- وظيفة لحساب بصمة الملف لضمان عدم التداخل ---
def get_file_hash(file):
    return hashlib.md5(file.getvalue()).hexdigest()

uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")

if uploaded_file:
    # 1. حساب بصمة الملف الحالي
    current_file_hash = get_file_hash(uploaded_file)
    
    # 2. التحقق: هل هذا الملف مختلف عن الملف السابق في الذاكرة؟
    if "file_hash" in st.session_state and st.session_state.file_hash != current_file_hash:
        # إذا كان ملفاً جديداً، نحذف البيانات القديمة تماماً
        if "vector_db" in st.session_state:
            del st.session_state.vector_db
        st.cache_resource.clear() # مسح الذاكرة المؤقتة للموارد

    # حفظ البصمة الحالية
    st.session_state.file_hash = current_file_hash

    # 3. إنشاء مجلد data إذا لم يكن موجوداً
    if not os.path.exists("data"):
        os.makedirs("data")
        
    file_path = os.path.join("data", "temp.pdf")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # 4. تحليل الملف إذا لم يكن موجوداً في الجلسة الحالية
    if 'vector_db' not in st.session_state:
        with st.spinner("جاري تحليل الملف الجديد... يرجى الانتظار"):
            try:
                st.session_state.vector_db = process_pdf(file_path)
                st.success("تم تحليل الملف الجديد بنجاح!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
                st.stop()

    # 5. واجهة السؤال والجواب
    query = st.text_input("ماذا تريد أن تعرف من هذا الملف؟", placeholder="مثال: لخص لي أهم النقاط في هذا الملف")
    
    if query:
        with st.spinner("جاري البحث في محتوى الملف..."):
            try:
                answer = ask_question(st.session_state.vector_db, query)
                st.markdown("### 📝 الإجابة:")
                st.info(answer)
            except Exception as e:
                st.error("حدث خطأ أثناء جلب الإجابة. تأكد من صحة مفتاح API.")
                
    # زر لمسح الجلسة والبدء من جديد
    if st.sidebar.button("🗑️ مسح الذاكرة والملفات"):
        st.session_state.clear()
        st.rerun()

else:
    st.info("👆 يرجى رفع ملف PDF للبدء.")
    # تنظيف الذاكرة في حال تم إزالة الملف
    if "vector_db" in st.session_state:
        st.session_state.clear()
