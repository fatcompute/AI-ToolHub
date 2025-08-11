import os
import sys
import torch
import argparse
import numpy as np
import evaluate
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, TextDataset, DataCollatorForLanguageModeling, TrainerCallback
from app import create_app
from models import db, TrainingJob, LLMModel, Dataset

# Custom Callback to save metrics to the database
class MetricsLoggerCallback(TrainerCallback):
    def __init__(self, job_id):
        self.job_id = job_id

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None:
            # Re-fetch the job in the current scope to append metrics
            job = TrainingJob.query.get(self.job_id)
            if job:
                # Ensure metrics is a list
                if job.metrics is None:
                    job.metrics = []

                # Append new log entry
                current_metrics = list(job.metrics)
                current_metrics.append(logs)
                job.metrics = current_metrics

                # Append to text logs as well
                job.logs += str(logs) + '\n'

                db.session.commit()

# --- Metrics Computation ---
accuracy_metric = evaluate.load("accuracy")
perplexity_metric = evaluate.load("perplexity")

def compute_metrics(eval_preds):
    logits, labels = eval_preds
    # The Trainer may shift logits and labels, we need to align them
    # Also, ignore padding index (-100)
    predictions = np.argmax(logits, axis=-1)

    # Filter out padding tokens
    true_predictions = predictions[labels != -100]
    true_labels = labels[labels != -100]

    # Compute accuracy
    accuracy = accuracy_metric.compute(predictions=true_predictions, references=true_labels)

    # Compute perplexity
    try:
        perplexity = perplexity_metric.compute(model_id='gpt2', predictions=logits)
        # The 'predictions' for perplexity are the raw logits
    except Exception as e:
        print(f"Could not compute perplexity: {e}")
        perplexity = {"perplexity": -1.0}

    return {
        "accuracy": accuracy.get('accuracy', -1.0),
        "perplexity": perplexity.get('perplexity', -1.0)
    }


def run_training(args):
    """
    The main function for the training process.
    This function is run in a separate process.
    """
    # Create a Flask app context to interact with the database
    app = create_app()
    with app.app_context():
        # 1. Fetch job details from the database
        job = TrainingJob.query.get(args.job_id)
        if not job:
            print(f"Error: Training job with ID {args.job_id} not found.")
            return

        try:
            # Update job status to 'running'
            job.status = 'running'
            job.logs = 'Training started...\n'
            db.session.commit()

            print(f"Starting training for job {args.job_id}...")

            # 2. Load base model and tokenizer
            print(f"Loading base model: {job.model.huggingface_id}")
            base_model_path = job.model.path
            tokenizer = AutoTokenizer.from_pretrained(base_model_path)
            model = AutoModelForCausalLM.from_pretrained(base_model_path)

            # Add a padding token if it doesn't exist
            if tokenizer.pad_token is None:
                tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                model.resize_token_embeddings(len(tokenizer))

            # 3. Load and prepare datasets
            print(f"Loading training dataset: {job.dataset.filename}")
            train_dataset = TextDataset(
                tokenizer=tokenizer,
                file_path=job.dataset.path,
                block_size=128
            )
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer, mlm=False
            )

            eval_dataset = None
            if args.eval_dataset_id:
                eval_dataset_record = Dataset.query.get(args.eval_dataset_id)
                if eval_dataset_record:
                    print(f"Loading evaluation dataset: {eval_dataset_record.filename}")
                    eval_dataset = TextDataset(
                        tokenizer=tokenizer,
                        file_path=eval_dataset_record.path,
                        block_size=128
                    )

            # 4. Configure Training Arguments
            output_dir = os.path.join(os.path.dirname(__file__), 'models', f"{job.model.name}_finetuned_job_{job.id}")

            training_args = TrainingArguments(
                output_dir=output_dir,
                overwrite_output_dir=True,
                num_train_epochs=args.num_train_epochs,
                per_device_train_batch_size=args.per_device_train_batch_size,
                save_steps=10_000,
                save_total_limit=2,
                logging_strategy="epoch",
                # Enable evaluation if a dataset is provided
                evaluation_strategy="epoch" if eval_dataset else "no",
            )

            # 5. Instantiate and run the Trainer
            metrics_callback = MetricsLoggerCallback(job_id=job_id)

            trainer = Trainer(
                model=model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                callbacks=[metrics_callback],
                compute_metrics=compute_metrics,
            )

            print("Trainer instantiated. Starting training...")
            job.logs += "Trainer initialized. Starting training...\n"
            db.session.commit()

            trainer.train()

            # 6. Save the fine-tuned model and update job status
            print("Training completed. Saving model...")
            trainer.save_model(output_dir)

            job.status = 'completed'
            job.logs += f"Training finished successfully. Model saved to {output_dir}\n"
            job.completed_at = db.func.now()
            db.session.commit()

            print(f"Job {job_id} finished successfully.")

        except Exception as e:
            # Handle any errors during the training process
            print(f"Error during training job {job_id}: {e}")
            job.status = 'failed'
            job.logs += f"\n\nERROR: {e}\n"
            db.session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a training job.")
    parser.add_argument("job_id", type=int, help="The ID of the training job in the database.")
    parser.add_argument("--eval_dataset_id", type=int, default=None, help="Optional ID of the evaluation dataset.")
    parser.add_argument("--num_train_epochs", type=int, default=1, help="Number of training epochs.")
    parser.add_argument("--per_device_train_batch_size", type=int, default=1, help="Batch size for training.")

    args = parser.parse_args()
    run_training(args)
