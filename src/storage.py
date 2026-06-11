import os
import shutil

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def _nb_dir(notebook_id: str) -> str:
    path = os.path.join(DATA_DIR, notebook_id)
    os.makedirs(path, exist_ok=True)
    return path


def _doc_path(notebook_id: str, doc_name: str) -> str:
    safe = doc_name.replace('/', '_').replace('\\', '_')
    return os.path.join(_nb_dir(notebook_id), safe + '.txt')


def index_document(notebook_id: str, doc_name: str, chunks: list) -> int:
    text = '\n\n'.join(chunks)
    with open(_doc_path(notebook_id, doc_name), 'w', encoding='utf-8') as f:
        f.write(text)
    return len(chunks)


def get_indexed_docs(notebook_id: str) -> list:
    nb_dir = os.path.join(DATA_DIR, notebook_id)
    if not os.path.exists(nb_dir):
        return []
    return sorted(
        fname[:-4]
        for fname in os.listdir(nb_dir)
        if fname.endswith('.txt')
    )


def get_doc_text(notebook_id: str, doc_name: str) -> str:
    path = _doc_path(notebook_id, doc_name)
    if not os.path.exists(path):
        return ''
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def get_full_text(notebook_id: str) -> str:
    nb_dir = os.path.join(DATA_DIR, notebook_id)
    if not os.path.exists(nb_dir):
        return ''
    texts = []
    for fname in sorted(os.listdir(nb_dir)):
        if fname.endswith('.txt'):
            with open(os.path.join(nb_dir, fname), 'r', encoding='utf-8') as f:
                texts.append(f.read())
    return '\n\n'.join(texts)


def delete_notebook_index(notebook_id: str) -> None:
    nb_dir = os.path.join(DATA_DIR, notebook_id)
    if os.path.exists(nb_dir):
        shutil.rmtree(nb_dir)
