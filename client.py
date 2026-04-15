#!/usr/bin/env python3
"""
Example client for interacting with Local LLM Server

Usage:
    python client.py "What is machine learning?"
    python client.py --stream "Write a poem about AI"
    python client.py --model mistral "Hello" --temp 0.5
"""

import argparse
import requests
import json
import sys
import time
from typing import Optional


class LocalLLMClient:
    """Client for Local LLM Server"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check server health"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"❌ Health check failed: {e}")
            return False

    def list_models(self) -> list:
        """Get available models"""
        try:
            response = self.session.get(f"{self.api_url}/models", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except requests.RequestException as e:
            print(f"❌ Failed to list models: {e}")
            return []

    def ask(
        self,
        prompt: str,
        model: str = "llama3",
        temperature: float = 0.7,
        num_predict: int = 256,
        stream: bool = False
    ) -> Optional[str]:
        """
        Ask the LLM a question

        Args:
            prompt: The prompt/question
            model: Model to use
            temperature: Sampling temperature (0-2)
            num_predict: Number of tokens to predict
            stream: Whether to stream response

        Returns:
            Generated response or None on error
        """
        payload = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "num_predict": num_predict,
            "stream": stream
        }

        endpoint = "/ask/stream" if stream else "/ask"

        try:
            response = self.session.post(
                f"{self.api_url}{endpoint}",
                json=payload,
                stream=stream,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()

            if stream:
                return self._handle_stream(response)
            else:
                return response.json().get("response")

        except requests.Timeout:
            print("❌ Request timed out. Try reducing num_predict or using streaming.")
            return None
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"   Detail: {error_data.get('detail', 'Unknown error')}")
                except:
                    pass
            return None

    def _handle_stream(self, response: requests.Response) -> str:
        """Handle streaming response"""
        print("🔄 Streaming response:", end=" ", flush=True)

        full_response = ""
        try:
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("token", "")
                        full_response += token
                        print(token, end="", flush=True)
                    except json.JSONDecodeError:
                        pass
        except requests.RequestException as e:
            print(f"\n❌ Streaming error: {e}")

        print("\n")
        return full_response


def main():
    parser = argparse.ArgumentParser(
        description="Client for Local LLM Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is AI?"
  %(prog)s --stream "Write a poem"
  %(prog)s --model mistral --temp 0.3 "Explain quantum computing"
  %(prog)s --check-health
        """
    )

    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt to send to the LLM"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "-m", "--model",
        default="llama3",
        help="Model to use (default: llama3)"
    )
    parser.add_argument(
        "-t", "--temp",
        type=float,
        default=0.7,
        help="Temperature (0-2, default: 0.7)"
    )
    parser.add_argument(
        "-n", "--num-predict",
        type=int,
        default=256,
        help="Number of tokens to predict (default: 256)"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream response tokens"
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Check server health"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models"
    )

    args = parser.parse_args()

    client = LocalLLMClient(args.base_url)

    # Check health
    if args.check_health:
        print("🔍 Checking server health...")
        if client.health_check():
            print("✅ Server is healthy!")
        else:
            print("❌ Server is not responding!")
            sys.exit(1)
        return

    # List models
    if args.list_models:
        print("📋 Available models:")
        models = client.list_models()
        if models:
            for model in models:
                print(f"  - {model}")
        else:
            print("  No models found or server not responding")
        return

    # Ask question
    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    print(f"🤔 Prompt: {args.prompt}")
    print(f"📦 Model: {args.model}")
    print(f"🌡️  Temperature: {args.temp}")
    print()

    start_time = time.time()
    response = client.ask(
        prompt=args.prompt,
        model=args.model,
        temperature=args.temp,
        num_predict=args.num_predict,
        stream=args.stream
    )

    if response:
        elapsed = time.time() - start_time
        print(f"\n⏱️  Response time: {elapsed:.2f}s")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
