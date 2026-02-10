import os
import pdfplumber
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# تحميل الإعدادات
load_dotenv()

def process_pdf(pdf_path):
    # 1. استخراج النص
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    
    docs = [Document(page_content=text)]
    
    # 2. تقسيم النص
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # --- الحل الجذري هنا ---
    # نستخدم معرفاً فريداً لكل عملية معالجة لضمان عدم تداخل البيانات
    import uuid
    unique_collection_name = f"pdf_coll_{uuid.uuid4().hex[:8]}"

    # إنشاء قاعدة البيانات مع التأكد من أنها كائن جديد تماماً
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings,
        collection_name=unique_collection_name,
        # إضافة persist_directory اختياري، ولكن تركه فارغاً مع اسم فريد يضمن الحذف عند إغلاق الجلسة
    )
    
    return vector_db

def ask_question(vector_db, query):
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0
    )
    
    # تحسين البحث: جلب أفضل 4 قطع نصية متعلقة بالسؤال
    docs = vector_db.similarity_search(query, k=4)
    context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    
    prompt = f"""
    أنت مساعد ذكي متخصص في تحليل النصوص. أجب على السؤال بناءً على النص في الملف المرفق فقط.
    
    التعليمات:
    1. صغ الإجابة بأسلوبك الخاص وبطريقة شرح واضحة.
    2. إذا لم تجد الإجابة في النص، قل "عذراً، هذه المعلومة غير متوفرة في الملف المرفوع حالياً".
    
    النص المرفق:
    {context}
    
    السؤال:
    {query}
    """
    
    response = llm.invoke(prompt)
    return response.content
