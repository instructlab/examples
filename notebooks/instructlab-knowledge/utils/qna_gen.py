# CELL 0
from pathlib import Path

from docling_sdg.qa.generate import Generator
from docling_sdg.qa.base import GenerateOptions, LlmProvider
from pydantic import SecretStr
import json
import yaml
import random
from textwrap import wrap

from docling_core.transforms.chunker.hierarchical_chunker import DocChunk, DocMeta
from docling_sdg.qa.utils import get_qa_chunks

API_KEY = "foo"
API_URL = "bar"
MODEL_ID = "baz"

generate_options = GenerateOptions(project_id="project_id")
generate_options.provider = LlmProvider.OPENAI_LIKE
generate_options.api_key = SecretStr(API_KEY)
generate_options.url = API_URL
generate_options.model_id = MODEL_ID

NUM_CHUNKS_PER_CONTRIBUTION_TO_SELECT_FOR_AUTHORING = 5

WORKSPACE_NAME = "default"

WORKSPACE_ROOT = Path("workspaces")
WORKSPACE_ROOT.mkdir(exist_ok=True)

WORKSPACE_DIR = WORKSPACE_ROOT / WORKSPACE_NAME
WORKSPACE_DIR.mkdir(exist_ok=True)

contribution_dirs = []
# contribution_names = ["nfl"]  # ADD CONTRIBUTION NAMES HERE
contribution_names = ["nfl", "finance"]

contribution_domain = "sports"
contribution_summary = "Official playing rules of the National Football League 2022"

# contribution1 = {"path": contribution_path, "prefix": contribution_prefix, "domain": contribution_domain, "summary": contribution_summary}
#contribution1 = {"path": contribution_path, "domain": contribution_domain, "summary": contribution_summary}

# contribution_path2 = Path(SOURCE_DOCUMENT_DIR / "finance")
# contribution_prefix2 = "finance"
# contribution_domain2 = "banking"
# contribution_summary2 = "Account information for a specific bank"

for name in contribution_names:
    contribution_dir = WORKSPACE_DIR / name
    contribution_dirs.append(contribution_dir)

print(f"Contribution names are: {contribution_names}")
print(f"Contribution dir are: {contribution_dirs}")

filters = [
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

dataset = {}
for contribution_name, contribution_dir in zip(contribution_names, contribution_dirs):
    dataset[contribution_name] = {}
    dataset[contribution_name]["chunks"] = []

    chunks_jsonl_path = contribution_dir / "chunks" / "chunks.jsonl"
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
        print(f"Chunking and filtering document {doc['file']}")
        
        qa_chunks = get_qa_chunks(doc["file"], doc["chunk_objs"], filters)
        dataset[contribution_name]["chunks"].extend(list(qa_chunks))

    generate_options.generated_file = contribution_dir / "authoring" / f"qagen-{contribution_name}.json"
    gen = Generator(generate_options=generate_options)


    l = dataset[contribution_name]["chunks"]
    print(f"ALI DEBUG: {len(l)}")
    selected_chunks = random.sample(l, NUM_CHUNKS_PER_CONTRIBUTION_TO_SELECT_FOR_AUTHORING)

    print(f"ALI DEBUG: {selected_chunks}")

    Path.unlink(generate_options.generated_file, missing_ok=True)
    results = gen.generate_from_chunks(selected_chunks) # automatically saves to file

    print(f"{contribution_name}: {results.status}")

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

    print(f"Generated QA pairs for {len(qnas)} contexts")
    print(list(qnas.values())[0])

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
    
    data['document_outline'] = contribution_summary
    data['domain'] = contribution_domain
    
    Path.unlink(qna_output_path, missing_ok=True) # shouldn't be necessary but was. jupyter caching thing?
    with open(qna_output_path, 'w') as yaml_file:
        yaml.dump(data, yaml_file, Dumper=IndentedDumper, default_flow_style=False, sort_keys=False, width=80)
    
    print(f"qna.yaml saved to: {qna_output_path}")
