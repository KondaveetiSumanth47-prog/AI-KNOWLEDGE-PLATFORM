def split_text(text, chunk_size=500, chunk_overlap=50):
    if not isinstance(text, str):
        text = str(text or "")

    cleaned_text = " ".join(text.split())

    if not cleaned_text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        chunk_overlap = 0

    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size - 1

    chunks = []
    start = 0
    text_length = len(cleaned_text)

    while start < text_length:
        target_end = min(start + chunk_size, text_length)

        if target_end == text_length:
            end = target_end
        else:
            sentence_end = -1

            for punctuation in [".", "?", "!"]:
                position = cleaned_text.rfind(punctuation, start, target_end)
                sentence_end = max(sentence_end, position)

            if sentence_end >= start + int(chunk_size * 0.6):
                end = sentence_end + 1
            else:
                word_end = cleaned_text.rfind(" ", start, target_end)

                if word_end >= start + int(chunk_size * 0.6):
                    end = word_end
                else:
                    end = target_end

        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        # If we ended at a sentence, start the next chunk cleanly.
        if cleaned_text[end - 1] in ".?!":
            start = end
        else:
            # Otherwise keep overlap, but begin at a complete word.
            overlap_start = max(start, end - chunk_overlap)

            while overlap_start > start and cleaned_text[overlap_start - 1] != " ":
                overlap_start -= 1

            start = overlap_start

    return chunks