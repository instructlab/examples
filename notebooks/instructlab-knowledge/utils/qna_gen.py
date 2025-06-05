import json
import yaml
import random

from pathlib import Path
from pydantic import SecretStr
from textwrap import wrap

from docling_core.transforms.chunker.hierarchical_chunker import DocChunk, DocMeta
from docling_sdg.qa.utils import get_qa_chunks
from docling_sdg.qa.generate import Generator
from docling_sdg.qa.base import GenerateOptions, LlmProvider

chunk_filter = [
    lambda chunk: len(str(chunk.text)) > 500
]

def str_presenter(dumper, data):
  if len(data.splitlines()) > 1:  # check for multiline string
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  elif len(data) > 80:
    data = "\n".join(wrap(data, 80))
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
  return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

# to use with safe_dump:
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

class IndentedDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentedDumper, self).increase_indent(flow, False)

def generate_seed_examples(contribution_name: str, contribution_dir: str, contribution_metadata: dict, num_seed_examples: int, api_key: str, api_url: str, model_id: str) -> Path:
    """
    Creates a seed dataset from a path
    Args:
        contribution_name (str):        Name of the contribution
        contribution_dir (str):         Path to the artifacts for the contribution. contribution_dir should contain
                                        a chunks/chunks.jsonl file
        contribution_metadata (dict):   Dictionary with the domain and summary of the contribution
        num_seed_examples (str):        Number of seed examples user wishes to generate for the contribution
        api_key (str):                  API key for the model used to generate questions and answers from contexts
        api_url (str):                  Endpoint for the model used to generate questions and answers from contexts
        model_id (str):                 Name of the model used to generate questions and answers from contexts
    Returns:
        qna_output_path (pathlib.Path): Path to the generated seed example file
    """
    dataset = {}
    dataset[contribution_name] = {}
    dataset[contribution_name]["chunks"] = []

    chunks_jsonl_path = contribution_dir / "chunks" / "chunks.jsonl"
    if not chunks_jsonl_path.exists():
        raise ValueError(f"chunks.jsonl does not exist but should at {chunks_jsonl_path}")

    docs = []

    with open(chunks_jsonl_path, 'r') as file:  # khaled was here
        for line in file:
            file_in_docs = False
            entry = json.loads(line)
            #entry = yaml.safe_load(line)
            meta = DocMeta(**entry['metadata'])
            chunk = DocChunk(text=entry['chunk'], meta=meta)
            for doc in docs:
                if doc["file"] == entry['file']:
                    doc["chunk_objs"].append(chunk)
                    file_in_docs = True
                    break

            if file_in_docs == False:
                doc = dict(file=entry['file'], chunk_objs=[chunk])
                docs.append(doc)

    for doc in docs:
        print(f"Filtering smaller chunks out of document {doc['file']}")
        
        qa_chunks = get_qa_chunks(doc["file"], doc["chunk_objs"], chunk_filter)
        dataset[contribution_name]["chunks"].extend(list(qa_chunks))


    l = dataset[contribution_name]["chunks"]
    selected_chunks = random.sample(l, num_seed_examples)

    generate_options = GenerateOptions(project_id="project_id")
    generate_options.provider = LlmProvider.OPENAI_LIKE
    generate_options.api_key = SecretStr(api_key)
    generate_options.url = api_url
    generate_options.model_id = model_id
    generate_options.generated_file = contribution_dir / "authoring" / f"qagen-{contribution_name}.json"
    gen = Generator(generate_options=generate_options)

    Path.unlink(generate_options.generated_file, missing_ok=True)
    results = gen.generate_from_chunks(selected_chunks) # automatically saves to file

    print(f"Status for Q&A generation for {contribution_name} is: {results.status}")

    qnas = {}
    chunk_id_to_text = {}
    with open(generate_options.generated_file, "rt") as f:
        for line in f.readlines():
            entry = json.loads(line)
            chunk_id = entry['chunk_id']
            if chunk_id not in chunk_id_to_text:
                chunk_id_to_text[chunk_id] = entry['context']
            if chunk_id not in qnas:
                qnas[chunk_id] = []
            qnas[chunk_id].append({'question': entry['question'], 'answer': entry['answer']})

    qna_output_path = contribution_dir / "authoring" / "qna.yaml"
    
    data = {'seed_examples': []}
    for chunk_id, context in chunk_id_to_text.items():
        data['seed_examples'].append({
            'context': context,
            'questions_and_answers': [
                {
                    'question': example['question'],
                    'answer': example['answer'],
                } for example in qnas[chunk_id]
            ]
        })
    
    data['document_outline'] = contribution_metadata["summary"]
    data['domain'] = contribution_metadata["domain"]
    
    Path.unlink(qna_output_path, missing_ok=True) # shouldn't be necessary but was. jupyter caching thing?
    with open(qna_output_path, 'w') as yaml_file:
        yaml.dump(data, yaml_file, Dumper=IndentedDumper, default_flow_style=False, sort_keys=False, width=80)
    
    return qna_output_path
