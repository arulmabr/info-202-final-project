# Curated list of ML ecosystem repositories to analyze
# Selected based on: popularity, clear dependency files, ML relevance

SEED_REPOS = [
    # Deep Learning Frameworks
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "jax-ml/jax",
    "keras-team/keras",
    "google/flax",
    "patrick-kidger/equinox",

    # Hugging Face ecosystem
    "huggingface/transformers",
    "huggingface/datasets",
    "huggingface/tokenizers",
    "huggingface/accelerate",
    "huggingface/diffusers",
    "huggingface/peft",
    "huggingface/safetensors",
    "huggingface/evaluate",

    # Traditional ML
    "scikit-learn/scikit-learn",
    "dmlc/xgboost",
    "microsoft/LightGBM",
    "catboost/catboost",
    "scikit-learn-contrib/imbalanced-learn",

    # Data processing
    "pandas-dev/pandas",
    "numpy/numpy",
    "pola-rs/polars",
    "apache/arrow",
    "h5py/h5py",
    "zarr-developers/zarr-python",

    # ML Tools & Experiment Tracking
    "wandb/wandb",
    "mlflow/mlflow",
    "optuna/optuna",
    "ray-project/ray",
    "Lightning-AI/pytorch-lightning",
    "fastai/fastai",
    "neptune-ai/neptune-client",
    "determined-ai/determined",

    # NLP
    "explosion/spaCy",
    "nltk/nltk",
    "facebookresearch/fairseq",
    "openai/tiktoken",
    "google/sentencepiece",
    "flairNLP/flair",
    "stanfordnlp/stanza",
    "argilla-io/argilla",

    # Computer Vision
    "opencv/opencv-python",
    "pytorch/vision",
    "albumentations-team/albumentations",
    "facebookresearch/detectron2",
    "ultralytics/ultralytics",
    "kornia/kornia",
    "open-mmlab/mmdetection",

    # Visualization
    "matplotlib/matplotlib",
    "plotly/plotly.py",
    "mwaskom/seaborn",
    "vega/altair",
    "bokeh/bokeh",

    # Utilities
    "tqdm/tqdm",
    "yaml/pyyaml",
    "psf/requests",
    "pallets/click",
    "tiangolo/typer",
    "pydantic/pydantic",
    "omry/omegaconf",
    "google/python-fire",

    # Numerical / Scientific
    "scipy/scipy",
    "sympy/sympy",
    "statsmodels/statsmodels",
    "pymc-devs/pymc",

    # Model serving / deployment
    "triton-inference-server/server",
    "bentoml/BentoML",
    "onnx/onnx",
    "microsoft/onnxruntime",
    "huggingface/text-generation-inference",

    # AutoML / HPO
    "automl/auto-sklearn",
    "keras-team/keras-tuner",
    "microsoft/nni",
    "autogluon/autogluon",

    # Feature engineering
    "alteryx/featuretools",
    "Feature-engine/feature_engine",

    # Time series
    "facebook/prophet",
    "sktime/sktime",
    "unit8co/darts",

    # Recommender systems
    "lenskit/lkpy",
    "NicolasHug/Surprise",
    "microsoft/recommenders",

    # Graph ML
    "pyg-team/pytorch_geometric",
    "dmlc/dgl",

    # Reinforcement Learning
    "DLR-RM/stable-baselines3",
    "Farama-Foundation/Gymnasium",

    # LLM tools
    "langchain-ai/langchain",
    "run-llama/llama_index",
    "vllm-project/vllm",

    # Audio
    "librosa/librosa",
    "speechbrain/speechbrain",

    # Testing / Quality
    "pytest-dev/pytest",
    "great-expectations/great_expectations",

    # Notebooks
    "jupyter/notebook",
    "jupyterlab/jupyterlab",

    # Distributed
    "dask/dask",
    "modin-project/modin",
    "vaexio/vaex",
    "fugue-project/fugue",
    "Eventual-Inc/Daft",
]


def get_seed_repos() -> list[str]:
    return SEED_REPOS.copy()
