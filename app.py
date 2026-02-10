import streamlit as st
from brain import process_pdf, ask_question
import os
import hashlib

# إعداد الصفحة
st.set_page_config(page_title="مساعد الـ PDF الذكي", page_icon="📚", layout="wide")
st.title("🤖 اسأل ملفاتك (نسخة Groq المجانية)")

def get_file_hash(file):
    return hashlib.md5(file.getvalue()).hexdigest()

uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")

if uploaded_file:
    current_file_hash = get_file_hash(uploaded_file)
    
    # التحقق مما إذا كان الملف قد تغير
    if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
        st.session_state.file_hash = current_file_hash
        # مسح قاعدة البيانات القديمة عند رفع ملف جديد
        if "vector_db" in st.session_state:
            del st.session_state.vector_db
        
        # إنشاء المجلد وحفظ الملف
        if not os.path.exists("data"):
            os.makedirs("data")
        
        file_path = os.path.join("data", f"{current_file_hash}.pdf") # اسم فريد للملف
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # معالجة الملف وتخزينه في الحالة
        with st.spinner("جاري تحليل الملف الجديد..."):
            try:
                st.session_state.vector_db = process_pdf(file_path)
                st.success("تم تحليل الملف بنجاح!")
            except Exception as e:
                st.error(f"خطأ في المعالجة: {e}")
                st.stop()

    # --- منطقة السؤال والجواب ---
    # نستخدم form لمنع إعادة التحميل العشوائي
    with st.form(key='qa_form'):
        query = st.text_input("ماذا تريد أن تعرف؟")
        submit_button = st.form_submit_button(label='إرسال')

    if submit_button and query:
        if 'vector_db' in st.session_state:
            with st.spinner("جاري البحث..."):
                try:
                    # تأكد أن دالة ask_question تستقبل vector_db والنص
                    answer = ask_question(st.session_state.vector_db, query)
                    st.markdown("### 📝 الإجابة:")
                    st.info(answer)
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")
        else:
            st.warning("لم يتم تحميل قاعدة البيانات، حاول إعادة رفع الملف.")

    # زر المسح في القائمة الجانبية
    if st.sidebar.button("🗑️ مسح الذاكرة"):
        st.session_state.clear()
        st.rerun()
else:
    st.info("👆 يرجى رفع ملف PDF للبدء.")
    # تنظيف الذاكرة إذا لم يوجد ملف مرفوع
    if "file_hash" in st.session_state:
        st.session_state.clear()
