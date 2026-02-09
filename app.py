import streamlit as st
from brain import process_pdf, ask_question
import os


st.set_page_config(page_title="مساعد الـ PDF الذكي", page_icon="📚")

st.title("🤖 اسأل ملفاتك (نسخة Groq المجانية)")

uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")

if uploaded_file:
    # إنشاء مجلد data إذا لم يكن موجوداً
    if not os.path.exists("data"):
        os.makedirs("data")
        
    file_path = os.path.join("data", "temp.pdf")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # حفظ قاعدة البيانات في الـ Session لكي لا يعيد التحليل مع كل سؤال
    if 'vector_db' not in st.session_state:
        with st.spinner("جاري تحليل الملف... قد يستغرق ذلك لحظات في المرة الأولى"):
            st.session_state.vector_db = process_pdf(file_path)
        st.success("تم التحليل بنجاح!")

    query = st.text_input("ماذا تريد أن تعرف من هذا الملف؟")
    
    if query:
        with st.spinner("جاري البحث عن الإجابة..."):
            answer = ask_question(st.session_state.vector_db, query)
            st.info("إليك الإجابة:")
            st.write(answer)