import os
import sys
import torch
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

def run_training(job_id):
    """
    The main function for the training process.
    This function is run in a separate process.
    """
    # Create a Flask app context to interact with the database
    app = create_app()
    with app.app_context():
        # 1. Fetch job details from the database
        job = TrainingJob.query.get(job_id)
        if not job:
            print(f"Error: Training job with ID {job_id} not found.")
            return

        try:
            # Update job status to 'running'
            job.status = 'running'
            job.logs = 'Training started...\n'
            db.session.commit()

            print(f"Starting training for job {job_id}...")

            # 2. Load base model and tokenizer
            print(f"Loading base model: {job.model.huggingface_id}")
            base_model_path = job.model.path
            tokenizer = AutoTokenizer.from_pretrained(base_model_path)
            model = AutoModelForCausalLM.from_pretrained(base_model_path)

            # Add a padding token if it doesn't exist
            if tokenizer.pad_token is None:
                tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                model.resize_token_embeddings(len(tokenizer))

            # 3. Load and prepare dataset
            print(f"Loading dataset: {job.dataset.filename}")
            dataset_path = job.dataset.path
            # For simplicity, we assume the dataset is a plain text file.
            # More advanced dataset handling would be needed for CSV/JSONL.
            train_dataset = TextDataset(
                tokenizer=tokenizer,
                file_path=dataset_path,
                block_size=128  # This should be a parameter in a real app
            )
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer, mlm=False
            )

            # 4. Configure Training Arguments
            output_dir = os.path.join(os.path.dirname(__file__), 'models', f"{job.model.name}_finetuned_job_{job.id}")

            training_args = TrainingArguments(
                output_dir=output_dir,
                overwrite_output_dir=True,
                num_train_epochs=1,  # Should be a parameter
                per_device_train_batch_size=1, # Should be a parameter
                save_steps=10_000,
                save_total_limit=2,
                logging_steps=100,
            )

            # 5. Instantiate and run the Trainer
            metrics_callback = MetricsLoggerCallback(job_id=job_id)

            trainer = Trainer(
                model=model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=train_dataset,
                callbacks=[metrics_callback],
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
    # This allows the script to be called from the command line with a job ID
    if len(sys.argv) > 1:
        job_id_arg = int(sys.argv[1])
        run_training(job_id_arg)
    else:
        print("Error: Please provide a training job ID.")
