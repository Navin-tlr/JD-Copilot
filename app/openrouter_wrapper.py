
import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

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
        print("Embedding vector (first 5 dimensions):
        print(embedding_response.data[0].embedding[:5])

    except (ValueError, openai.APIError) as e:
        print(f"An error occurred: {e}")
