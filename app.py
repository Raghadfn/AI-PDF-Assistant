import streamlit as st
from brain import process_pdf, ask_question
import os
import hashlib
import shutil

# 1. إعداد الصفحة
st.set_page_config(page_title="مساعد الـ PDF الذكي", page_icon="📚", layout="wide")
st.title("🤖 اسأل ملفاتك (نسخة Groq المجانية)")

# وظيفة لحساب بصمة الملف الفريدة
def get_file_hash(file):
    return hashlib.md5(file.getvalue()).hexdigest()

# وظيفة لتنظيف مجلد البيانات لضمان عدم تراكم الملفات القديمة
def clear_data_folder():
    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data")

uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")

if uploaded_file:
    # حساب بصمة الملف الحالي
    current_file_hash = get_file_hash(uploaded_file)
    
    # التحقق: هل الملف المرفوع حالياً يختلف عما هو مخزن في الجلسة؟
    if "current_hash" not in st.session_state or st.session_state.current_hash != current_file_hash:
        # إذا كان ملفاً جديداً (أو عاد للملف الأول):
        with st.spinner("🔄 جاري تبديل الملف وتحليل البيانات الجديدة..."):
            # تنظيف المجلد لضمان عدم وجود ملفات temp قديمة
            clear_data_folder()
            
            # حفظ الملف الجديد باسمه الفريد
            file_path = os.path.join("data", f"{current_file_hash}.pdf")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # معالجة الملف وتحديث الـ session_state
            try:
                # نقوم بمسح الذاكرة المؤقتة لـ Streamlit يدوياً لضمان إعادة المعالجة
                st.cache_resource.clear() 
                
                st.session_state.vector_db = process_pdf(file_path)
                st.session_state.current_hash = current_file_hash
                st.success("✅ تم تحديث محتوى الذاكرة بناءً على الملف الحالي!")
            except Exception as e:
                st.error(f"❌ خطأ في المعالجة: {e}")
                st.stop()

    # --- منطقة الأسئلة (استخدام الـ Form ضروري لثبات الواجهة) ---
    st.divider()
    with st.form(key='qa_form', clear_on_submit=False):
        query = st.text_input(f"🔍 اسأل عن محتوى الملف (بصمة: {st.session_state.current_hash[:8]}):")
        submit_button = st.form_submit_button(label='إرسال السؤال')

    if submit_button and query:
        if 'vector_db' in st.session_state:
            with st.spinner("🧠 جاري استخراج الإجابة..."):
                try:
                    answer = ask_question(st.session_state.vector_db, query)
                    st.markdown("### 📝 الإجابة:")
                    st.info(answer)
                except Exception as e:
                    st.error(f"⚠️ حدث خطأ أثناء جلب الإجابة: {e}")
        else:
            st.warning("⚠️ لا توجد بيانات محملة. يرجى إعادة رفع الملف.")

    # زر المسح الشامل في القائمة الجانبية
    if st.sidebar.button("🗑️ مسح الذاكرة بالكامل"):
        clear_data_folder()
        st.session_state.clear()
        st.rerun()

else:
    # إذا لم يكن هناك ملف مرفوع، نقوم بتصفير الحالة
    if "current_hash" in st.session_state:
        st.session_state.clear()
    st.info("👆 يرجى رفع ملف PDF للبدء.")
