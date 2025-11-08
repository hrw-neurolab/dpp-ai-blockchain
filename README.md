# dpp-ai-blockchain

## TL;DR

This repository implements a full pipeline to simulate the AI-assisted mapping of Digital Product Passport (DPP) data, which is gathered from 10 imaginary production machines over a six-month period and then stored on the Waves Blockchain. The dataset is automatically generated and cached on the first run. The goal is to measure an LLM's reliability in mapping dynamic and unstructured JSON data at a large scale into a standardized target JSON format, while assessing 3 different prompting techniques. The correctly mapped data points will be stored on a public ledger using smart contracts to present a tamper-evident storage solution for DPP-data. The entire process is monitored to investigate the speed and overall applicability of such a solution in real production environments.

## 📘 Detailed Description of the Repository

The repository includes the following implementations:

<details>
  <summary>
    Dataset Preparation
  </summary>

- The dataset is **automatically generated** on the first run and then **cached** for subsequent use
- Synthetic time-series data is generated for 10 imaginary production machines, covering the first 6 months of 2024 (approximately 180 samples per machine, one datapoint per machine per day)
- The target dataset follows a standardized JSON format for all samples, containing metrics such as:
  - Energy consumption, material usage, CO2 emissions, water consumption
  - Operating parameters (temperature, humidity, vibration, etc.)
  - Production output and maintenance status
- The source dataset simulates real-world scenarios where each machine is subject to a specific schema variation, resulting in 10 different schema variations which the LLM has to map to the target schema
- Three main properties are varied throughout the data: `Field Name (key)`, `Value Type` and `Value Unit`
- Three difficulty levels are provided: `simple`, `moderate`, and `complex`, each with varying degrees of schema variations and complexity:
  - **Simple**: Basic schema variations with 8 core metrics
  - **Moderate**: Extended schema with 16 metrics and more complex variations
  - **Complex**: Full complexity with all metrics and advanced perturbations
- The prepared datasets are automatically stored in `data/{difficulty}/` directories, with separate files for source data, target data, and few-shot examples
- To ensure reproducibility, a global seed of `42` is used in numpy and random for generating the synthetic data and perturbations

</details>

<details>
  <summary>
    JSON Mapping via LLMs
  </summary>

- Three types of prompts are investigated:
  - Zero-shot prompting: The LLM shall directly map new incoming JSON data, optionally given a target schema description (based on the Pydantic model)
  - Few-shot prompting: The LLM shall directly map new incoming JSON data given examples of correct mappings between source and target samples
  - Mapping-function prompting: The LLM shall generate one python function for each of the 10 variations, which then can be used to correctly map all inputs to the target format. The prompt includes basic instructions and the target schema (based on the Pydantic model)
- The script uses the [Langchain library](https://python.langchain.com/) to dynamically generate the prompts based on predefined templates and invoke the LLM accordingly
- To compare different LLMs, the script (currently) includes models provided by OpenAI and locally served models via ollama, but can theoretically be extended to all models supported by Langchain
- Supports multiple structured output modes: `function_calling`, `json_mode`, and `json_schema` for better output control
- Includes an iterative refinement mechanism for Ollama models to improve mapping accuracy through multiple attempts
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

cp src/blockchain/blockchain_connector/.env.example src/blockchain/blockchain_connector/.env
# Paste your Waves seed
```

3. (Only for ollama usage) Pull your desired model in the ollama CLI tool:

```bash
ollama pull gemma3:4b
```

Alternatively, you can use Docker Compose to run multiple Ollama instances with GPU support:

```bash
docker-compose -f docker-compose.ollama.yml up -d
```

## 🚀 Usage

The script can be executed by running `python main.py`. To ensure full flexibility, the command accepts multiple flags, of which some are required to be set:

### Required Arguments

```
--model-provider {openai,ollama}
                      The provider of the LLM model to use for evaluation.
--model-name MODEL_NAME
                      The name of the LLM model to use for evaluation.
--prompt {zero-shot,few-shot,mapping-function}
                      The prompt type to use for evaluation.
--difficulty {simple,moderate,complex}
                      The difficulty level of the dataset to use for evaluation.
```

### Optional Arguments

```
--resume RESUME       The path to a previous run's output directory to resume from.
--include-schema      Flag to indicate whether to include the schema in the prompt.
--output-dir OUTPUT_DIR
                      Directory to save the processed output files. (default: ./output)
--cache-dir CACHE_DIR
                      Directory to cache the datasets and few-shot prompts. (default: ./data)
--num-samples NUM_SAMPLES
                      Number of samples to use for evaluation. If None, all samples will be used.
--blockchain          Flag to indicate whether to push the parsed data to the blockchain.
--ollama-host OLLAMA_HOST
                      Host address for the Ollama model server. (default: 127.0.0.1:11434)
--max-refinement-attempts MAX_REFINEMENT_ATTEMPTS
                      Maximum number of refinement attempts for the model. (default: 0)
--structured-output {function_calling,json_mode,json_schema}
                      Structured output mode for the model. Not applicable to `mapping-function` prompt.
--wrap-thinking       Whether to wrap the thinking content in a separate field in the output.
                      (Only for structured output modes)
```

### Examples

Basic usage with OpenAI:
```bash
python main.py --model-provider openai --model-name gpt-4o --prompt zero-shot --difficulty simple
```

Using Ollama with few-shot prompting and schema:
```bash
python main.py --model-provider ollama --model-name gemma3:12b --prompt few-shot --difficulty moderate --include-schema
```

With blockchain integration and limited samples:
```bash
python main.py --model-provider openai --model-name gpt-4o --prompt mapping-function --difficulty complex --blockchain --num-samples 100
```

Resume a previous run:
```bash
python main.py --resume ./output/gpt-4o/2025-01-15_10-30-45_simple_zero-shot
```

When using OpenAI or ollama models, the `model-provider` must be set to `openai` or `ollama`, respectively.
When using ollama, the specified model (e.g. `gemma3:4b`) must already be pulled to the local machine in advance.
