# dpp-ai-blockchain

## TL;DR

This repository implements a full pipeline to simulate the AI-assisted mapping of Digital Product Passport (DPP) data, which is gathered from 10 imaginary production machines over a one-year period and then stored on the Waves Blockchain. The goal is to measure an LLMs reliability in mapping dynamic and unstructured JSON data at a large scale into a standardized target JSON format, while assessing 3 different prompting techniques. The correctly mapped data points will be stored on a public ledger using smart contracts to present a tamper-evident storage solution for DPP-data. The entire process is monitored to investigate the speed and overall applicability of such a solution in real production environments.

## 📘 Detailed Description of the Repository

The repository includes the following implementations:

<details>
  <summary>
    Dataset Preparation
  </summary>

- Downloading the open-source Kaggle dataset ["sustainable-manufacturing-large-data"](https://www.kaggle.com/datasets/lastman0800/sustainable-manufacturing-large-data)
- Cleaning up the duplicated data, resulting in 1 sample for each of the 10 machines
- Generating imaginary time-series data based on the given mean and standard deviation, resulting in 365 samples for each of the 10 machines (one datapoint per machine per day)
- Generating the target dataset based on a standardized JSON format for all samples
- Generating the source dataset: The original JSON data is augmented to simulate a scenario, where each machine is subject to a specific schema variation, resulting in 10 different schema variations which the LLM has to map to the target schema
- Three main properties are varied throughout the data: `Field Name (key)`, `Value Type` and `Value Unit`
- For easier comprehension of the dataset preparation process, the script is written as a Jupyter Notebook, which allows a step-by-step execution of the individual code cells
- To ensure reproducibility, a global seed of `42` was used in numpy for generating the random perturbations

</details>

<details>
  <summary>
    JSON Mapping via LLMs
  </summary>

- Three types of prompts are investigated:
  - Schema-based prompting: The LLM shall directly map new incoming JSON data given a target schema description (based on the Pydantic model)
  - Few-shot prompting: The LLM shall directly map new incoming JSON data given 4 examples of correct mappings between source and target samples
  - Mapping-function prompting: The LLM shall generate one python function for each of the 10 variations, which then can be used to correctly map all inputs to the target format. The prompt includes basic instructions and the target schema (based on the Pydantic model)
- The script uses the [Langchain library](https://python.langchain.com/) to dynamically generate the prompts based on predefined templates and invoke the LLM accordingly
- To compare different LLMs, the script (currently) includes models provided by OpenAI and locally served models via ollama, but can theoretically be extended to all models supported by Langchain
- To ensure proper evaluation, each raw result is stored locally in `.jsonl` or `.json` format, along with the configuration and prompt template of the experiment

</details>

<details>
  <summary>
    Data Storage and Aggregation on the Waves Blockchain
  </summary>

- To simulate a real environment, the parsed data of each imaginary production day is stored on the [Waves Blockchain](https://waves.tech/)
- Each of the 10 production machines is allocated to a unique blockchain address / account, so that the per-day-data can always be traced back to the respective machine.
- A Smart Contract is implemented to upload the per-day (one sample) data to the respective address.
- Another  Smart Contract is implemented, which, on request, accumulates the required data from all machines for a specific production day and returns the aggregated result. The result can be used to verify sustainability claims inside of a DPP either on batch, or on product entity level.
- The setup enables full flexibility for
  - How many machines are involved
  - The data collection frequency (e.g. per day, per hour, per produced unit)
  - How the stored data is aggregated to enable verified sustainability claims in a DPP

</details>

<details>
  <summary>
    Evaluation
  </summary>

- The evaluation pipeline is separated from the main pipeline to ensure a proper speed comparison for production environments
- During the mapping of JSON data via LLMs, several problems may occur. The different problem types occurred during running the pipeline on all samples are categorized and logged properly
- The evaluation script then calculates basic statistics of problem type occurrences, execution times, and stores them in a new JSON file located in the corresponding experiment directory

</details>

## 🔧 Setup

### Prerequisites

In order to run the scripts without conflicts or other issues, the following prerequisites are recommended:

- UNIX-based Operating System, but also works on Windows 11
- [ollama](https://ollama.ai/download) installed locally on the machine
- A CUDA-capable GPU (if ollama tests will be run)
- An OpenAI API Key (if GPT tests will be run)
- Python Version >= 3.12
- An individual virtual environment (venv or conda) for this repository

The repository has been verified working within the following environments:

- Windows Subsystem for Linux (WSL)
  - WSL Version `2.4.13.0`
  - Ubuntu Version `24.04.2 LTS`
  - Kernel Version `5.15.167.4-1`
  - Python Version `3.12.9`
- Windows 11
  - Version `24H2`
  - Build `26100.3775`
  - Python Version `3.12.7`
- Ubuntu Server
  - Ubuntu Version `22.04.5 LTS`
  - Kernel Version `6.2.0-26-generic`
  - Python Version `3.12.4`

### Installation

1. Generate a virtual environment and install the required libraries (Example for Linux & venv):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create the necessary .env files:

```bash
cp .env.example .env
# Paste your OpenAI API Key

cp WavesConnector/.env.example WavesConnector/.env
# Paste your Waves seed
```

3. (Only for ollama usage) Pull your desired model in the ollama CLI tool:

```bash
ollama pull gemma3:4b
```

### Dataset Recreation

Even though the dataset files are already located in this repository, you may want to comprehend the creation process.
To exactly recreate the dataset files, which are stored at `dataset/*.json`, open up the [Jupyter Notebook](dataset/preparation.ipynb). Now, either execute every cell one-by-one or click on `Run All`.

## 🚀 Usage

The script can be executed by running `python main.py`. To ensure full flexibility, the command accepts multiple flags, of which some are required to be set:

```
--output-dir OUTPUT_DIR
                      Directory to save the processed output files.
--model-provider {openai,ollama} *required
                      The provider of the LLM model to use for evaluation.
--model-name MODEL_NAME *required
                      The name of the LLM model to use for evaluation.
--prompt {few_shot,schema_driven,mapping_function} *required
                      The prompt type to use for evaluation.
--single-sample       Run the evaluation on a single sample instead of the entire dataset.
```

When using OpenAI or ollama models, the `model-provider` must be set to `openai` or `ollama`, respectively.
When using ollama, the specified model (e.g. `gemma3:4b`) must already be pulled to the local machine in advance.
The `--single-sample` command is only for testing and ensures, that only the very first sample will be processed through the pipeline.
