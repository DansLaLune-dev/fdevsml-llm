from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

class AtomicRAG:
    # Changez 'doc_path' par 'data_folder' ici :
    def __init__(self, data_folder):
        # ... restez cohérent dans le corps de la fonction
        
        # 1. Initialisation des Embeddings (déjà corrigé précédemment)
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': False}
        
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
        except Exception:
            import sentence_transformers
            sentence_transformers.SentenceTransformer(model_name)
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        # --- AJOUT CRITIQUE ICI ---
        # 2. Initialisation de l'attribut par défaut pour éviter l'AttributeError
        self.vectorstore = None
        
        # 3. Lancement automatique de la préparation de la DB
        self._prepare_db(data_folder)

    def _prepare_db(self, doc_path):
        if not os.path.exists(doc_path):
            print(f"Attention: {doc_path} non trouvé.")
            return

        with open(doc_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n### ", "\n#### ", "\n```fpdevsml", "\n```", "\n\n", "\n"]
        )
        chunks = text_splitter.create_documents([text])
        
        # Création de la vectorstore
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )

    def get_context(self, query: str, k=5):
        # Maintenant, self.vectorstore existe (soit None, soit l'objet Chroma)
        if self.vectorstore is None:
            return ""
        
        search_results = self.vectorstore.similarity_search(query, k=k)
        return "\n--- CONTEXTE DE RÉFÉRENCE ---\n" + "\n".join([doc.page_content for doc in search_results])