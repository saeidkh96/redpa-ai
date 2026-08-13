import re


class ChunkingService:
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200

    def __init__(
        self,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(
        self,
        text: str,
    ) -> list[str]:
        normalized_text = self._normalize_text(text)

        if not normalized_text:
            return []

        if len(normalized_text) <= self.chunk_size:
            return [normalized_text]

        chunks: list[str] = []
        start = 0
        text_length = len(normalized_text)

        while start < text_length:
            ideal_end = min(
                start + self.chunk_size,
                text_length,
            )

            end = self._find_split_position(
                text=normalized_text,
                start=start,
                ideal_end=ideal_end,
            )

            chunk = normalized_text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = end - self.chunk_overlap

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    def _find_split_position(
        self,
        *,
        text: str,
        start: int,
        ideal_end: int,
    ) -> int:
        if ideal_end >= len(text):
            return len(text)

        minimum_end = start + int(
            self.chunk_size * 0.6
        )

        separators = (
            "\n\n",
            "\n",
            ". ",
            "! ",
            "? ",
            "; ",
            ", ",
            " ",
        )

        for separator in separators:
            position = text.rfind(
                separator,
                minimum_end,
                ideal_end,
            )

            if position != -1:
                return position + len(separator)

        return ideal_end

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()