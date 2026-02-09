import os
import pdfplumber
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document # هذا السطر مهم جداً


# تحميل الإعدادات
load_dotenv()

def process_pdf(pdf_path):
    # استخدام pdfplumber لقراءة النصوص العربية بدقة أعلى
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    
    # تحويل النص المستخرج إلى تنسيق يفهمه LangChain
    docs = [Document(page_content=text)]
    
    # تقسيم النص
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma.from_documents(chunks, embeddings)
    
    return vector_db

def ask_question(vector_db, query):
    # استخدام الموديل الأحدث والأكثر استقراراً
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant", # استخدم هذا الموديل لأنه أسرع وأقل هلوسة
        temperature=0
    )
    
    docs = vector_db.similarity_search(query)
    context = "\n".join([doc.page_content for doc in docs])
    
    prompt = f"""
    أنت مساعد ذكي متخصص في تحليل النصوص. أجب على السؤال بناءً على النص المرفق فقط.
    
    تعليمات هامة:
    1. صغ الإجابة بأسلوبك الخاص وبطريقة شرح واضحة و كلمات مفهومه.
    2. لا تكتفِ بنسخ الروابط الإلكترونية أو حقوق النشر إلا إذا سُئلت عنها.
    3. إذا لم تجد الإجابة في النص، قل "عذراً، هذه المعلومة غير متوفرة".
    
    النص المستخرج من الملف:
    {context}
    
    السؤال:
    {query}
    """
    
    response = llm.invoke(prompt)
    return response.content