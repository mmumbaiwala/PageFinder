import lmdb
import pickle
from typing import Optional


class LmdbDocumentStore:
    def __init__(self, path: str, map_size_bytes: int = 10 * 1024**3):
        self.env = lmdb.open(
            path,
            map_size=map_size_bytes,
            max_dbs=3,
            subdir=True,
            lock=True
        )
        # Named DBs
        self.docs_db = self.env.open_db(b"docs")
        self.digital_db = self.env.open_db(b"digital_pages")
        self.ocr_db = self.env.open_db(b"ocr_pages")

    def _encode_key(self, doc_id: str, page: Optional[int] = None) -> bytes:
        if page is not None:
            return f"{doc_id}_page_{page:04}".encode()
        return doc_id.encode()

    def save_document_metadata(self, doc_id: str, file_path: str, file_name: str, metadata: dict):
        data = {
            "file_path": file_path,
            "file_name": file_name,
            "metadata": metadata
        }
        with self.env.begin(write=True, db=self.docs_db) as txn:
            txn.put(doc_id.encode(), pickle.dumps(data))

    def save_page_texts(self, doc_id: str, page: int, digital_text: Optional[str], ocr_text: Optional[str]):
        key = self._encode_key(doc_id, page)
        with self.env.begin(write=True) as txn:
            if digital_text is not None:
                txn.put(key, pickle.dumps(digital_text), db=self.digital_db)
            if ocr_text is not None:
                txn.put(key, pickle.dumps(ocr_text), db=self.ocr_db)

    def get_document_metadata(self, doc_id: str) -> Optional[dict]:
        with self.env.begin(db=self.docs_db) as txn:
            raw = txn.get(doc_id.encode())
            return pickle.loads(raw) if raw else None

    def get_page_digital_text(self, doc_id: str, page: int) -> Optional[str]:
        key = self._encode_key(doc_id, page)
        with self.env.begin(db=self.digital_db) as txn:
            raw = txn.get(key)
            return pickle.loads(raw) if raw else None

    def get_page_ocr_text(self, doc_id: str, page: int) -> Optional[str]:
        key = self._encode_key(doc_id, page)
        with self.env.begin(db=self.ocr_db) as txn:
            raw = txn.get(key)
            return pickle.loads(raw) if raw else None

    def list_all_docs(self) -> list[str]:
        with self.env.begin(db=self.docs_db) as txn:
            return [key.decode() for key, _ in txn.cursor()]

    def close(self):
        self.env.close()

if __name__ == "__main__":
    db = LmdbDocumentStore("document_store.lmdb")

    doc_id = "doc_001"
    db.save_document_metadata(doc_id, "/files/doc.pdf", "doc.pdf", {"lang": "eng", "pages": 3})

    db.save_page_texts(doc_id, 1, digital_text="This is page 1 digital", ocr_text="OCR page 1")
    db.save_page_texts(doc_id, 2, digital_text="This is page 2 digital", ocr_text="OCR page 2")

    print(db.get_document_metadata(doc_id))
    print("Digital page 1:", db.get_page_digital_text(doc_id, 1))
    print("OCR page 1:", db.get_page_ocr_text(doc_id, 1))

    print("Available docs:", db.list_all_docs())

    db.close()
