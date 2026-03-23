import os
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download


def main():
    parser = argparse.ArgumentParser(
        description="Download a Hugging Face model."
    )

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Hugging Face model repo ID (e.g. unsloth/Llama-OuteTTS-1.0-1B)",
    )

    parser.add_argument(
        "--output-base",
        type=str,
        default="models",
        help="Base directory where models are stored (default: models/)",
    )

    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Hugging Face token (optional, falls back to HF_TOKEN env var)",
    )

    args = parser.parse_args()

    # Resolve token
    hf_token = args.token or os.getenv("HF_TOKEN")

    if not hf_token:
        raise RuntimeError(
            "No Hugging Face token provided.\n"
            "Use --token or set HF_TOKEN environment variable.\n"
            "Or run: hf auth login"
        )

    # Extract model name (after slash)
    model_name = args.model.split("/")[-1]

    # Build output path
    output_dir = Path(args.output_base) / model_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading model: {args.model}")
    print(f"Saving to: {output_dir}")

    snapshot_download(
        repo_id=args.model,
        local_dir=str(output_dir),
        local_dir_use_symlinks=False,
        token=hf_token,
    )

    print(f"✅ Model saved to {output_dir}")


if __name__ == "__main__":
    main()
#
