"""Emotion CT Pipeline — CLI entry point."""
import json
import logging
import os

import typer

from finetune.application.usecases.build_datasets import BuildDatasetsUseCase
from finetune.application.usecases.collect_data import CollectDataUseCase
from finetune.application.usecases.decide_promotion import DecidePromotionUseCase
from finetune.application.usecases.label_data import LabelDataUseCase
from finetune.application.usecases.run_evaluation import RunEvaluationUseCase
from finetune.application.usecases.run_training import RunTrainingUseCase
from finetune.domain.services.dataset_builder import DatasetBuilderService
from finetune.domain.services.label_agreement import LabelAgreementService
from finetune.domain.services.promotion_decider import PromotionDeciderService, PromotionPolicy
from finetune.infrastructure.data_sources.csv_loader import CsvDataSourceLoader
from finetune.infrastructure.data_sources.distilabel_labeler import DistilabelLabeler
from finetune.infrastructure.evaluation.sklearn_evaluator import SklearnEvaluator
from finetune.infrastructure.repositories.file_dataset_repository import FileDatasetRepository
from finetune.infrastructure.training.config_loader import ConfigLoader
from finetune.infrastructure.training.unsloth_trainer import UnslothTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/pipeline.log"),
    ],
)

app = typer.Typer(name="finetune", help="Emotion Continuous Training Pipeline")


@app.command()
def collect(source: str = typer.Option("data/raw/extract.csv", help="Path to CSV file")):
    """Stage 1: Load raw data from CSV."""
    loader = CsvDataSourceLoader()
    usecase = CollectDataUseCase(data_source=loader)
    samples = usecase.execute(source)
    typer.echo(f"Loaded {len(samples)} samples from {source}")

    repo = FileDatasetRepository()
    repo.save_samples(samples, "data/labeled/raw_samples.jsonl")
    typer.echo("Saved to data/labeled/raw_samples.jsonl")


@app.command()
def label(
    input_path: str = typer.Option("data/labeled/raw_samples.jsonl"),
    model: str = typer.Option("gpt-4o-mini"),
):
    """Stage 2: AI label + 3-way agreement."""
    repo = FileDatasetRepository()
    samples = repo.load_samples(input_path)
    typer.echo(f"Loaded {len(samples)} samples for labeling")

    labeler = DistilabelLabeler(model=model)
    agreement = LabelAgreementService()
    usecase = LabelDataUseCase(labeler=labeler, agreement_service=agreement)

    approved, flagged = usecase.execute(samples)
    typer.echo(f"Approved: {len(approved)}, Flagged: {len(flagged)}")

    repo.save_samples(approved, "data/labeled/agreed/approved.jsonl")
    repo.save_samples(flagged, "data/labeled/agreed/flagged.jsonl")


@app.command()
def build(version: str = typer.Option("v1.0", help="Dataset version tag")):
    """Stage 3: Build train/val/test splits."""
    repo = FileDatasetRepository()
    samples = repo.load_samples("data/labeled/agreed/approved.jsonl")
    typer.echo(f"Building dataset v{version} from {len(samples)} approved samples")

    builder = DatasetBuilderService()
    usecase = BuildDatasetsUseCase(
        builder=builder,
        dataset_repo=repo,
        output_base="data/datasets",
    )
    dataset_version = usecase.execute(samples, version=version)
    typer.echo(
        f"Dataset built: train={dataset_version.train_count}, "
        f"val={dataset_version.val_count}, test={dataset_version.test_count}"
    )


@app.command()
def train(
    version: str = typer.Option("v1.0", help="Dataset version to train on"),
    config: str = typer.Option("qwen2.5_1.5b_lora", help="Training config name"),
):
    """Stage 4: Fine-tune with Unsloth."""
    config_loader = ConfigLoader()
    cfg = config_loader.load(config)

    dataset_path = f"data/datasets/{version}"
    trainer = UnslothTrainer()
    usecase = RunTrainingUseCase(trainer=trainer)

    typer.echo(f"Starting training with config={config}, dataset={version}")
    run = usecase.execute(dataset_path, cfg)
    typer.echo(f"Training complete. Run ID: {run.run_id}, Status: {run.status}")


@app.command()
def evaluate(
    model_path: str = typer.Option("data/artifacts/latest", help="Path to model"),
    version: str = typer.Option("v1.0", help="Dataset version for benchmark"),
    regression: bool = typer.Option(True, help="Run regression tests"),
    report_dir: str = typer.Option("data/artifacts/latest", help="Directory for eval report"),
):
    """Stage 5: Evaluate model and generate report."""
    evaluator = SklearnEvaluator()
    usecase = RunEvaluationUseCase(evaluator=evaluator)

    benchmark_path = f"data/datasets/{version}/test.jsonl"
    regression_path = "data/datasets/regression/regression_test.jsonl" if regression else None

    typer.echo(f"Evaluating {model_path} on {benchmark_path}")
    result = usecase.execute(model_path, benchmark_path, regression_path)
    typer.echo(f"Accuracy: {result.accuracy:.4f}, F1 Macro: {result.f1_macro:.4f}")
    typer.echo(f"Benchmark size: {result.benchmark_size}")

    from finetune.infrastructure.evaluation.report_generator import ReportGenerator
    report_gen = ReportGenerator()
    report = report_gen.generate(result)
    report_path = os.path.join(report_dir, "eval_report.md")
    report_gen.save(report, report_path)
    typer.echo(f"Report saved to {report_path}")

    eval_path = os.path.join(report_dir, "eval_result.json")
    os.makedirs(os.path.dirname(eval_path) or ".", exist_ok=True)
    with open(eval_path, "w") as f:
        json.dump({
            "accuracy": result.accuracy,
            "f1_macro": result.f1_macro,
            "f1_per_class": result.f1_per_class,
            "confusion_matrix": result.confusion_matrix,
            "regression_pass_rate": result.regression_pass_rate,
            "benchmark_size": result.benchmark_size,
            "eval_time_seconds": result.eval_time_seconds,
        }, f, indent=2)


@app.command()
def decide(
    candidate_path: str = typer.Option("data/artifacts/latest/eval_result.json"),
    baseline_path: str = typer.Option("data/artifacts/baseline/eval_result.json"),
):
    """Stage 5b: Promote or reject candidate model."""
    with open(candidate_path) as f:
        candidate_data = json.load(f)
    with open(baseline_path) as f:
        baseline_data = json.load(f)

    from finetune.domain.entities import EvalResult
    candidate_eval = EvalResult(**candidate_data)
    baseline_eval = EvalResult(**baseline_data)

    policy = PromotionPolicy()
    decider = PromotionDeciderService(policy=policy)
    usecase = DecidePromotionUseCase(decider=decider)

    promote, reason = usecase.execute(candidate_eval, baseline_eval)
    if promote:
        typer.echo(f"PROMOTE: {reason}")
    else:
        typer.echo(f"REJECT: {reason}", err=True)
        raise typer.Exit(1)


@app.command()
def publish(
    model_path: str = typer.Option(..., help="Path to quantized model"),
    version: str = typer.Option(..., help="Version tag (e.g. v1.1.0)"),
    eval_report: str = typer.Option(None, help="Path to eval report markdown"),
    hf: bool = typer.Option(True, help="Push to HuggingFace Hub"),
    mlflow_log: bool = typer.Option(False, help="Register in MLflow"),
):
    """Stage 6: Publish promoted model to registry."""
    if hf:
        from finetune.infrastructure.registry.huggingface_publisher import HuggingFacePublisher
        publisher = HuggingFacePublisher()
        url = publisher.publish(model_path, version, eval_report)
        typer.echo(f"Published to HuggingFace: {url}")

    if mlflow_log:
        from finetune.infrastructure.registry.mlflow_registry import MLflowRegistry
        registry = MLflowRegistry()
        uri = registry.publish(model_path, version)
        typer.echo(f"Registered in MLflow: {uri}")


@app.command()
def quantize(
    adapter_path: str = typer.Option(..., help="Path to LoRA adapter"),
    base_model: str = typer.Option("Qwen/Qwen2.5-1.5B-Instruct"),
    output_dir: str = typer.Option("data/artifacts/quantized"),
):
    """Stage 6 helper: Merge LoRA + AWQ quantize."""
    from finetune.infrastructure.packaging.awq_quantizer import AWQQuantizer
    quantizer = AWQQuantizer()
    quant_path = quantizer.merge_and_quantize(
        base_model=base_model,
        adapter_path=adapter_path,
        output_path=output_dir,
    )
    typer.echo(f"Quantized model at: {quant_path}")


@app.command()
def pipeline(
    source: str = typer.Option("data/raw/extract.csv"),
    config: str = typer.Option("qwen2.5_1.5b_lora"),
    version: str = typer.Option("v1.0"),
):
    """Run full pipeline Stage 1 → 6."""
    typer.echo("=== Starting full pipeline ===")
    collect(source=source)
    label()
    build(version=version)
    train(version=version, config=config)
    evaluate(version=version)
    decide()
    typer.echo("=== Pipeline complete ===")


if __name__ == "__main__":
    app()
