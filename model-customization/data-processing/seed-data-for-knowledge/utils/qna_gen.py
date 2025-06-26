import json
import yaml
import random

from pathlib import Path

from docling_sdg.qa.prompts.generation_prompts import QaPromptTemplate
from pydantic import SecretStr
from textwrap import wrap

from docling_core.transforms.chunker.hierarchical_chunker import DocChunk, DocMeta
from docling_sdg.qa.utils import get_qa_chunks
from docling_sdg.qa.generate import Generator
from docling_sdg.qa.base import GenerateOptions, LlmProvider

CUSTOM_COMBINED_QUESTION_PROMPT =  (
    "I will provide you a text passage. I need you to generate three questions that "
    "must be answered only with information contained in this passage, and nothing "
    "else.\n"
    'The first question is of type "fact_single", which means that the answer to this '
    "question is a simple, single piece of factual information contained in the "
    "context.\n"
    'The second question is of type "summary", which means that the answer to this '
    "question summarizes different pieces of factual information contained in the "
    "context.\n"
    'The third question is of type "reasoning", which is a question that requires the '
    "reader to think critically and make an inference or draw a conclusion based on "
    "the information provided in the passage.\n"
    "Make sure that the three questions are different. Make sure that every question "
    " has a provided answer\n\n"
    "{customization_str}\n\n"
    "You will format your generation as a python dictionary, such as:\n\n"
    '{"fact_single": <The "fact_single" type question you thought of>, '
    '"fact_single_answer: <Answer to the "fact_single" question>, "summary": <the '
    '"summary" type question you thought of>, "summary_answer": <Answer to the '
    '"summary" question>, "reasoning": <the "reasoning" type question you thought '
    'of>, "reasoning_answer": <Answer to the "reasoning" question>}\n\n'
    "Only provide the python dictionary as your output. Make sure you provide an answer for each question.\n\n"
    "Context: {context_str}"
)

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

def save_random_chunk_selection(chunks_jsonl_path: Path, output_dir: Path, num_seed_examples: int) -> Path:
    """
    Creates a seed dataset from a path
    Args:
        chunks_jsonl_path (Path):       Path to the chunks.jsonl file
        output_dir (Path):              Path to output dir for select_chunks.jsonl
        num_seed_examples (int):        Number of chunks user wishes to randomly select
    Returns:
        selected_chunks_file_path (pathlib.Path): Path to the generated seed example file
    """
    if not chunks_jsonl_path.exists():
        raise ValueError(f"chunks.jsonl does not exist but should at {chunks_jsonl_path}")

    chunks = []

    with open(chunks_jsonl_path, 'r') as file:  # khaled was here
        for line in file:
            chunk = json.loads(line)
            chunks.append(chunk)

    selected_chunks = random.sample(chunks, num_seed_examples)

    selected_chunks_file_path = output_dir / "selected_chunks.jsonl"
    with open(selected_chunks_file_path, "w", encoding="utf-8") as file:
        for chunk in selected_chunks:
            json.dump(chunk, file)
            file.write("\n")

    return selected_chunks_file_path

def generate_seed_examples(contribution_name: str, chunks_jsonl_path: Path, output_dir: Path, api_key: str, api_url: str, model_id: str, domain: str, summary: str, customization_str: str | None = None) -> Path:
    """
    Generates questions and answers per chunk via docling sdg. Saves them in an intermediate file
    Args:
        contribution_name (str):        Name of the contribution
        chunks_jsonl_path (Path):       Path to the chunks/chunks.jsonl file
        output_dir (Path):              Path to output dir for the qna.yaml and intermediate outputs by docling-sdg
        api_key (str):                  API key for the model used to generate questions and answers from contexts
        api_url (str):                  Endpoint for the model used to generate questions and answers from contexts
        model_id (str):                 Name of the model used to generate questions and answers from contexts
        customization_str (str | None)  A directive for how to stylistically customize the generated QAs
    Returns:
        qna_output_path (pathlib.Path): Path to a json file for generated questions and answers
    """
    dataset = {}
    dataset[contribution_name] = {}
    dataset[contribution_name]["chunks"] = []

    if not chunks_jsonl_path.exists():
        raise ValueError(f"chunks file does not exist but should at {chunks_jsonl_path}")

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
        print(f"Filtering smaller chunks out of chunks from document {doc['file']}")

        qa_chunks = get_qa_chunks(doc["file"], doc["chunk_objs"], chunk_filter)
        dataset[contribution_name]["chunks"].extend(list(qa_chunks))


    selected_chunks = dataset[contribution_name]["chunks"]

    generate_options = GenerateOptions(project_id="project_id")
    generate_options.provider = LlmProvider.OPENAI_LIKE
    generate_options.api_key = SecretStr(api_key)
    generate_options.url = api_url
    generate_options.model_id = model_id
    generate_options.generated_file = output_dir / f"qagen-{contribution_name}.json"

    if customization_str is not None:
        generate_options.prompts = [QaPromptTemplate(
            template=CUSTOM_COMBINED_QUESTION_PROMPT,
            keys=["context_str", "customization_str"],
            labels=["fact_single", "summary", "reasoning"],
            type_="question",
        )]

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

    qna_output_path = output_dir / "qna.yaml"

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


    data['document_outline'] = summary
    data['domain'] = domain

    Path.unlink(qna_output_path, missing_ok=True) # shouldn't be necessary but was. jupyter caching thing?
    with open(qna_output_path, 'w') as yaml_file:
        yaml.dump(data, yaml_file, Dumper=IndentedDumper, default_flow_style=False, sort_keys=False, width=80)

    return qna_output_path

def review_seed_examples_file(seed_examples_path: Path, min_seed_examples: int = 5, num_qa_pairs: int = 3) -> None:
    """
    Review a seed example file has the expected number of fieldds
    Args:
        seed_examples_path (Path):      Path to the qna.yaml file
        min_seed_example (int):         Minimum number of expected seed examples
        num_qa_pairs (int):             Number of expected question and answer pairs in a seed example
    Returns:
        None
    """
    with open(seed_examples_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
        errors = []
        print(f"Reviewing seed examples file at {seed_examples_path.resolve()}")

        # Check for document_outline
        if 'document_outline' not in yaml_data:
            errors.append("Missing contribution summary in 'document_outline'")
        else:
            # contribution summary is called document_outline internally
            print(f"Found contribution summary...")

        # Check for domain
        if 'domain' not in yaml_data:
            errors.append("Missing 'domain'")
        else:
            print(f"Found 'domain'...")

        # Check seed_examples
        seed_examples = yaml_data.get('seed_examples')
        if not seed_examples:
            errors.append("'seed_examples' section is missing or empty.")
        elif len(seed_examples) < min_seed_examples:
            errors.append(f"'seed_examples' should contain at least {min_seed_examples} examples, found {len(seed_examples)}. Please add {min_seed_examples - len(seed_examples)} more seed example(s)")
        else:
            print(f"Found {len(seed_examples)} 'contexts' in 'sed_examples'. Minimum expected number is {min_seed_examples}...")

        if seed_examples:
            for i, example in enumerate(seed_examples, start=1):
                qa_pairs = example.get('questions_and_answers')
                if not qa_pairs:
                    errors.append(f"Seed Example {i} is missing 'questions_and_answers' section.")
                elif len(qa_pairs) != num_qa_pairs:
                    errors.append(f"Seed Example {i} should contain {num_qa_pairs} question-answer pairs, found {len(qa_pairs)}. Please add {num_qa_pairs - len(qa_pairs)} more question-answer pair(s) to seed example {i}")
                else:
                    print(f"Seed Example {i} contains expected number ({num_qa_pairs}) of 'question_and_answers'...")

        if errors:
            print("\n\033[31mERROR! Seed Examples validation failed with the following issues:\033[0m")
            for err in errors:
                print(f"- {err}")
        else:
            print(f"Seed Examples YAML {seed_examples_path.resolve()} is valid :)")
        print(f"\n")



def view_seed_example(qna_output_path: Path, seed_example_num: int) -> None:
    """
    View a specific seed example in a qna.yaml
    Args:
        qna_output_path (Path):         Path to the qna.yaml file
        seed_example_num (int):         index of seed example to view
    Returns:
        None
    """

    with open(qna_output_path, "r") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
        seed_examples = yaml_data.get('seed_examples')
        if seed_example_num >= len(seed_examples):
            raise ValueError(f"seed_example_num must be less than number of seed examples {len(seed_examples)}")
        seed_example = seed_examples[seed_example_num]
        print("Context:")
        print(f"{seed_example["context"]}\n")
        for qna in seed_example["questions_and_answers"]:
            print(f"Question: {qna["question"]}")
            print(f"Answer: {qna["answer"]}\n")
