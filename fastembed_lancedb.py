"""
Offiziell dokumentiertes Custom-Embedding-Function-Pattern von lancedb
(siehe https://docs.lancedb.com/embedding -> "Custom Embedding Functions"),
angewendet auf `fastembed` (ONNX Runtime, kein PyTorch), das lancedb selbst
seit einiger Zeit nicht mehr eingebaut mitliefert.

Nutzung:

    import fastembed_lancedb  # registriert "fastembed"
    from lancedb.embeddings import get_registry

    embeddingFunction = get_registry().get("fastembed").create(
        name="BAAI/bge-small-en-v1.5"
    )
"""

from functools import cached_property

from lancedb.embeddings import TextEmbeddingFunction, register


@register("fastembed")
class FastEmbedEmbeddings(TextEmbeddingFunction):
    name: str = "BAAI/bge-small-en-v1.5"
    max_length: int = 512

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [e.tolist() for e in self._model.embed(list(texts))]

    def ndims(self) -> int:
        return len(self.generate_embeddings(["test"])[0])

    @cached_property
    def _model(self):
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=self.name, max_length=self.max_length)
