# rag_engine.py
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class AtomicRAG:
    def __init__(self, doc_path="README.md"):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        #self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
        self.vectorstore = None
        self._prepare_db(doc_path)

    def _prepare_db(self, doc_path):
        if not os.path.exists(doc_path):
            print(f"Attention: {doc_path} non trouvé.")
            return

        with open(doc_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=[
                "\n### ",
                "\n#### ",
                "\n```fpdevsml",
                "\n```",
                "\n\n",
                "\n"
            ]
        )
        docs = text_splitter.create_documents([text])
        self.vectorstore = FAISS.from_documents(docs, self.embeddings)

    def get_context(self, query: str, k=5):
        if not self.vectorstore:
            return ""
        search_results = self.vectorstore.similarity_search(query, k=k)
        return "\n--- CONTEXTE DE RÉFÉRENCE ---\n" + "\n".join([doc.page_content for doc in search_results])