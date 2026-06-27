"""
Pipeline RAG para consulta aos manuais técnicos da turbina KY-9000.
Indexa documentos Markdown no ChromaDB e realiza busca semântica.
"""
import os
from pathlib import Path

import chromadb
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

DIR_DOCUMENTOS = Path(__file__).parent.parent.parent / "documentos"
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
COLECAO = "kymera-manuais"
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_URL,
    )


def _cliente_chroma() -> chromadb.HttpClient:
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)


def indexar_documentos(forcar: bool = False) -> int:
    """
    Lê os documentos Markdown, divide em chunks e indexa no ChromaDB.

    Args:
        forcar: se True, recria a coleção mesmo que já exista.

    Returns:
        Número de chunks indexados.
    """
    cliente = _cliente_chroma()

    colecoes = [c.name for c in cliente.list_collections()]
    if COLECAO in colecoes and not forcar:
        col = cliente.get_collection(COLECAO)
        total = col.count()
        print(f"Coleção '{COLECAO}' já existe com {total} chunks. Use forcar=True para reindexar.")
        return total

    if COLECAO in colecoes:
        cliente.delete_collection(COLECAO)

    splitter_md = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "titulo"),
            ("##", "secao"),
            ("###", "subsecao"),
        ]
    )

    splitter_texto = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", " "],
    )

    documentos: list[Document] = []
    arquivos = list(DIR_DOCUMENTOS.glob("*.md"))

    for arquivo in arquivos:
        texto = arquivo.read_text(encoding="utf-8")
        chunks_md = splitter_md.split_text(texto)
        chunks_finais = splitter_texto.split_documents(chunks_md)

        for chunk in chunks_finais:
            chunk.metadata["arquivo"] = arquivo.name

        documentos.extend(chunks_finais)
        print(f"  {arquivo.name}: {len(chunks_finais)} chunks")

    print(f"\nIndexando {len(documentos)} chunks no ChromaDB...")

    vectorstore = Chroma.from_documents(
        documents=documentos,
        embedding=_embeddings(),
        client=cliente,
        collection_name=COLECAO,
    )

    print(f"Indexação concluída. Total: {len(documentos)} chunks.")
    return len(documentos)


def buscar(pergunta: str, k: int = 4) -> list[dict]:
    """
    Busca os chunks mais relevantes para a pergunta.

    Args:
        pergunta: texto da consulta em linguagem natural.
        k: número de resultados a retornar.

    Returns:
        Lista de dicts com 'conteudo', 'arquivo' e 'score'.
    """
    cliente = _cliente_chroma()

    vectorstore = Chroma(
        client=cliente,
        collection_name=COLECAO,
        embedding_function=_embeddings(),
    )

    resultados = vectorstore.similarity_search_with_score(pergunta, k=k)

    return [
        {
            "conteudo": doc.page_content,
            "arquivo": doc.metadata.get("arquivo", "desconhecido"),
            "score": round(float(score), 4),
        }
        for doc, score in resultados
    ]


if __name__ == "__main__":
    print("Indexando documentos técnicos...")
    total = indexar_documentos(forcar=True)
    print(f"\nTeste de busca:")
    resultados = buscar("o que fazer quando eficiencia_hpc cai?")
    for r in resultados:
        print(f"\n[{r['arquivo']}] score={r['score']}")
        print(r["conteudo"][:200])
