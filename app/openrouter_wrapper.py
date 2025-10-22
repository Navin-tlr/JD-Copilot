class OpenRouterWrapper:
    """
    A wrapper class for interacting with the OpenRouter API.
    """

    def __init__(self):
        """
        Initializes the OpenRouter client.
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            # Explicitly fail-fast with a helpful message. OpenRouter is optional; prefer Gemini
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured. OpenRouter features are optional — set OPENROUTER_API_KEY to enable, or use the Gemini client (GEMINI_API_KEY) as the primary LLM."
            )

        # Initialize HTTP client wrapper for OpenRouter-compatible endpoints
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def get_completion(self, messages, model="meta-llama/llama-3-8b-instruct"):
        """
        Gets a chat completion from a specified model.

        Args:
            messages (list): A list of message dictionaries (e.g., [{"role": "user", "content": "Hello"}]).
            model (str): The model to use for the completion.

        Returns:
            A chat completion object.
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
        )

    def chat(self, messages, max_tokens=3000, temperature=0.7, model="meta-llama/llama-3-8b-instruct"):
        """
        Gets a chat completion and returns the text directly, matching Gemini interface.

        Args:
            messages (list): A list of message dictionaries (e.g., [{"role": "user", "content": "Hello"}]).
            max_tokens (int): Maximum tokens in response.
            temperature (float): Sampling temperature.
            model (str): The model to use for the completion.

        Returns:
            str: The generated text response.
        """
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if completion.choices:
            return completion.choices[0].message.content or ""
        return ""

    def get_embedding(self, text, model="text-embedding-ada-002"):
        """
        Gets an embedding for a given text.

        Args:
            text (str): The text to embed.
            model (str): The embedding model to use.

        Returns:
            An embedding object.
        """
        return self.client.embeddings.create(
            input=[text],
            model=model
        )


def get_openrouter_client(model: str = "meta-llama/llama-3-8b-instruct") -> OpenRouterWrapper:
    """Factory function to get an OpenRouter client instance."""
    return OpenRouterWrapper()

import os
import openai

class OpenRouterWrapper:
    """
    A wrapper class for interacting with the OpenRouter API.
    """

    def __init__(self):
        """
        Initializes the OpenRouter client.
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env file")

        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def get_completion(self, messages, model="meta-llama/llama-3-8b-instruct"):
        """
        Gets a chat completion from a specified model.

        Args:
            messages (list): A list of message dictionaries (e.g., [{"role": "user", "content": "Hello"}]).
            model (str): The model to use for the completion.

        Returns:
            A chat completion object.
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
        )

    def chat(self, messages, max_tokens=3000, temperature=0.7, model="meta-llama/llama-3-8b-instruct"):
        """
        Gets a chat completion and returns the text directly, matching Gemini interface.

        Args:
            messages (list): A list of message dictionaries (e.g., [{"role": "user", "content": "Hello"}]).
            max_tokens (int): Maximum tokens in response.
            temperature (float): Sampling temperature.
            model (str): The model to use for the completion.

        Returns:
            str: The generated text response.
        """
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if completion.choices:
            return completion.choices[0].message.content or ""
        return ""

    def get_embedding(self, text, model="text-embedding-ada-002"):
        """
        Gets an embedding for a given text.

        Args:
            text (str): The text to embed.
            model (str): The embedding model to use.

        Returns:
            An embedding object.
        """
        return self.client.embeddings.create(
            input=[text],
            model=model
        )

# Example usage:
if __name__ == "__main__":
    try:
        # This assumes you have OPENROUTER_API_KEY set in your .env file
        wrapper = OpenRouterWrapper()

        # Example chat completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ]
        completion = wrapper.get_completion(messages)
        if completion.choices:
            print("Chat completion response:")
            print(completion.choices[0].message.content)
        else:
            print("No response for chat completion.")

        print("-" * 20)

        # Example embedding
        embedding_response = wrapper.get_embedding("Hello, world!")
        print("Embedding vector (first 5 dimensions):")
        print(embedding_response.data[0].embedding[:5])

    except (ValueError, openai.APIError) as e:
        print(f"An error occurred: {e}")
