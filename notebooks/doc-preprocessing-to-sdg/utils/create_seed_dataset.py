# Standard
from pathlib import Path
import json
import re
from typing import List, Dict

# Third Party
from datasets import Dataset, concatenate_datasets
from transformers import AutoTokenizer
import yaml

def get_seed_dataset(path: str) -> Dataset:
  print(f"Going into {path} at the top")
  dirs = get_dirs(path)
  datasets = []
  for path in dirs:
      ds = create_dataset_from_dir(path)
      datasets.append(ds)

  return safe_concatenate_datasets(datasets)

def get_dirs(path: str) -> List:
    """
    Returns a list of directories that contain a qna.yaml and one or more .txt chunks
    """
    base_path = Path(path)
    if not base_path.is_dir():
        raise ValueError("Base path must be a directory")

    print(f"Going into {base_path}")

    dirs = []

    files = list(base_path.iterdir())
    has_qna = any(f.name == 'qna.yaml' for f in files)
    has_txt = any(f.suffix == '.txt' for f in files)
    if has_qna and has_txt:
        dirs.append(base_path)
    else:
      print(f"Skipping {directory} no qna.yaml or .txt chunks")

    if len(dirs) == 0:
        raise ValueError("No Directories contain a qna.yaml and chunks")

    return dirs

def read_chunks(path: Path) -> Dict:
    """
    Returns a dictionary with all of the .txt chunks in a directory
    The chunks may originate from one or more different files
    """
    chunk_files = path.glob('*.txt')

    chunks_dict = {}
    for file in chunk_files:
        chunks = []
        match = re.match(r"^(.*?)[-_]\d+\.txt$", file.name)
        if match:
            orig_filename = match.group(1)

            with file.open('r', encoding='utf-8') as f:
                chunk = f.read()

            if orig_filename not in chunks_dict:
                chunks_dict[orig_filename] = []
            chunks_dict[orig_filename].append(chunk)

        else:
            print(f"Ignoring .txt file {file}, file name is not the right format")

    return chunks_dict

def create_dataset_from_dir(path: Path) -> Dataset:
    """
    Process the parsed docling json file and return a dataset.
    Args:
        json_fp (str): Path to the parsed docling json file.
    Returns:
        Dataset: Dataset object.
    """

    qna_yaml_path = path / "qna.yaml"

    with open(qna_yaml_path, 'r') as f:
      qna_yaml = yaml.safe_load(f)

    # Check for required fields
    if not all(key in qna_yaml for key in ['document_outline', 'domain', 'seed_examples']):
        raise ValueError("qna.yaml file is missing document_outline, domain, or seed_examples fields")

    chunks_dict = read_chunks(path)
    
    datasets = []
    for filename in chunks_dict.keys():
      chunks = chunks_dict[filename]
      chunk_ds = Dataset.from_dict(
          {
              "document": chunks,
              "document_outline": [qna_yaml["document_outline"]]
              * len(chunks),
              "document_title": [filename] * len(chunks), # TODO: is this really a necessary field?
              "domain": [qna_yaml["domain"]] * len(chunks),
          }
      )
      chunk_ds_with_icls = add_icls(qna_yaml, chunk_ds)
      datasets.append(chunk_ds_with_icls)

    return safe_concatenate_datasets(datasets)

def safe_concatenate_datasets(datasets: list):
    """
    Concatenate datasets safely, ignoring any datasets that are None or empty.
    """
    filtered_datasets = [ds for ds in datasets if ds is not None and ds.num_rows > 0]

    if not filtered_datasets:
        return None

    return concatenate_datasets(filtered_datasets)

def get_token_count(text, tokenizer):
    return len(tokenizer.tokenize(text))

def add_icls(qna_yaml: Dict, chunked_document: Dataset) -> Dataset:
    """
    Add the ICLS label to the dataset.
    Args:
        dataset (Dataset): Dataset object.
    Returns:
        Dataset: Dataset object with ICLS label.
    """
    # TODO: make the tokenizer configurable at some level
    tokenizer = AutoTokenizer.from_pretrained("instructlab/granite-7b-lab")
    icl = qna_yaml["seed_examples"]
    chunked_document_all_icl = []
    for icl_ in icl:
        chunked_document_all_icl.append(
            chunked_document.map(
                lambda x: {
                    "icl_document": icl_["context"],
                    "icl_query_1": icl_["questions_and_answers"][0]["question"],
                    "icl_response_1": icl_["questions_and_answers"][0]["answer"],
                    "icl_query_2": icl_["questions_and_answers"][1]["question"],
                    "icl_response_2": icl_["questions_and_answers"][1]["answer"],
                    "icl_query_3": icl_["questions_and_answers"][2]["question"],
                    "icl_response_3": icl_["questions_and_answers"][2]["answer"],
                }
            )
        )
    chunked_document_all_icl = safe_concatenate_datasets(chunked_document_all_icl)
    chunked_document_all_icl = chunked_document_all_icl.map(
        lambda x: {
            "chunks": chunk_document(
                [x["document"]], server_ctx_size=4096, chunk_word_count=1024
            )
            if get_token_count(x["document"], tokenizer) > 1024
            else [x["document"]]
        }
    )
    df = chunked_document_all_icl.to_pandas()
    df_exploded = df.explode("chunks").reset_index(drop=True)
    new_ds = Dataset.from_pandas(df_exploded)
    new_ds = new_ds.remove_columns("document").rename_columns(
        {"chunks": "document"}
    )

    # Only keep document greater than 100 tokens
    new_ds = new_ds.filter(
        lambda x: get_token_count(x["document"], tokenizer) > 100
    )
    return new_ds
