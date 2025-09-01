import lmdb
import pickle
from typing import Optional, List, Tuple, Dict


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
            **metadata  # <-- Unpack the metadata directly
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

    def save_page_texts_batch(self, doc_id: str, page_texts: List[Tuple[Optional[str], Optional[str]]]):
        """
        Save multiple pages in a single transaction for better performance.
        
        Args:
            doc_id: Document identifier
            page_texts: List of tuples (digital_text, ocr_text) for each page
        """
        with self.env.begin(write=True) as txn:
            for page_num, (digital_text, ocr_text) in enumerate(page_texts, 1):
                key = self._encode_key(doc_id, page_num)
                if digital_text is not None:
                    txn.put(key, pickle.dumps(digital_text), db=self.digital_db)
                if ocr_text is not None:
                    txn.put(key, pickle.dumps(ocr_text), db=self.ocr_db)

    def get_document_metadata(self, doc_id: str) -> Optional[dict]:
        with self.env.begin(db=self.docs_db) as txn:
            raw = txn.get(doc_id.encode())
            if raw:
                data = pickle.loads(raw)
                # Handle both old and new metadata formats
                if "metadata" in data:
                    # Old format: {"file_path": "...", "file_name": "...", "metadata": {...}}
                    return {
                        "file_path": data.get("file_path", ""),
                        "file_name": data.get("file_name", ""),
                        **data.get("metadata", {})
                    }
                else:
                    # New format: direct unpacking
                    return data
            return None

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

    def get_document_pages(self, doc_id: str, prefer: str = "digital", combine: bool = True) -> Dict[int, str]:
        """
        Return a mapping of page_number -> text for a document.

        Args:
            doc_id: Document identifier
            prefer: Which source to prefer when both exist: "digital" or "ocr"
            combine: If True, concatenate digital and OCR text when both exist

        Returns:
            Dict of {page_num: text}
        """
        pages: Dict[int, str] = {}

        # Gather digital texts
        with self.env.begin(db=self.digital_db) as txn:
            cursor = txn.cursor()
            prefix = f"{doc_id}_page_".encode()
            if cursor.first():
                for k, v in cursor:
                    if not k.startswith(prefix):
                        continue
                    try:
                        page_str = k.decode().rsplit("_", 1)[-1]
                        page_num = int(page_str)
                    except Exception:
                        continue
                    pages[page_num] = pickle.loads(v) if v else ""

        # Merge OCR texts
        with self.env.begin(db=self.ocr_db) as txn:
            cursor = txn.cursor()
            prefix = f"{doc_id}_page_".encode()
            if cursor.first():
                for k, v in cursor:
                    if not k.startswith(prefix):
                        continue
                    try:
                        page_str = k.decode().rsplit("_", 1)[-1]
                        page_num = int(page_str)
                    except Exception:
                        continue
                    ocr_text = pickle.loads(v) if v else ""
                    if page_num in pages:
                        if combine:
                            # Combine texts if different
                            digital_text = pages[page_num] or ""
                            if ocr_text and ocr_text not in digital_text:
                                pages[page_num] = (digital_text + "\n" + ocr_text).strip()
                        else:
                            if prefer.lower() == "ocr" and ocr_text:
                                pages[page_num] = ocr_text
                    else:
                        pages[page_num] = ocr_text

        return pages

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
