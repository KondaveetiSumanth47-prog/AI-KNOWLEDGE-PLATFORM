import re


def split_text(text, chunk_size=500, chunk_overlap=50):
    """
    Split text into chunks prioritizing paragraph and sentence boundaries,
    ensuring no words are truncated, overlap is applied safely without duplicates,
    and invalid arguments and edge cases are handled robustly.
    """
    if not isinstance(text, str):
        text = str(text or "")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        chunk_overlap = 0

    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size - 1

    # Normalize carriage returns and strip surrounding whitespace
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    # If text contains double newlines, treat them as paragraph delimiters
    has_paragraphs = "\n\n" in normalized
    if has_paragraphs:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
    else:
        # Single block of text
        paragraphs = [normalized]

    cleaned_paragraphs = []
    for p in paragraphs:
        cleaned_p = " ".join(p.split())
        if cleaned_p:
            cleaned_paragraphs.append(cleaned_p)

    if not cleaned_paragraphs:
        return []

    # Short document check: if the entire text fits in one chunk, return it immediately
    full_text = " ".join(cleaned_paragraphs) if not has_paragraphs else "\n\n".join(cleaned_paragraphs)
    if len(full_text) <= chunk_size:
        return [full_text]

    # Helper to split an oversized sentence / word sequence safely without infinite loops
    def _split_oversized(content, limit, overlap):
        words = content.split()
        if not words:
            return []
        sub_chunks = []
        curr_words = []
        curr_len = 0
        idx = 0

        while idx < len(words):
            word = words[idx]
            if len(word) > limit:
                if curr_words:
                    sub_chunks.append(" ".join(curr_words))
                    curr_words = []
                    curr_len = 0
                step = limit - overlap if limit > overlap else limit
                for char_start in range(0, len(word), max(1, step)):
                    sub_chunks.append(word[char_start:char_start + limit])
                idx += 1
                continue

            add_len = len(word) if curr_len == 0 else curr_len + 1 + len(word)
            if add_len <= limit:
                curr_words.append(word)
                curr_len = add_len
                idx += 1
            else:
                if curr_words:
                    sub_chunks.append(" ".join(curr_words))
                    # Overlap with previous words
                    overlap_words = []
                    overlap_len = 0
                    for prev_word in reversed(curr_words):
                        test_len = len(prev_word) if overlap_len == 0 else overlap_len + 1 + len(prev_word)
                        if test_len <= overlap:
                            overlap_words.insert(0, prev_word)
                            overlap_len = test_len
                        else:
                            break
                    curr_words = list(overlap_words)
                    curr_len = overlap_len
                else:
                    curr_words.append(word)
                    curr_len = len(word)
                    idx += 1

        if curr_words:
            sub_chunks.append(" ".join(curr_words))
        return sub_chunks

    # Split a paragraph into sentences
    sentence_regex = re.compile(r'(?<=[.!?])\s+')

    def _split_into_sentences(text_block):
        raw = sentence_regex.split(text_block)
        return [s.strip() for s in raw if s.strip()]

    chunks = []

    # If the document has structured paragraphs, respect them so distinct topics aren't mashed
    if has_paragraphs and len(cleaned_paragraphs) > 1:
        current_block = ""
        for p in cleaned_paragraphs:
            # If paragraph is very short (like a heading < 50 chars), attach to current
            if len(p) <= chunk_size:
                if not current_block:
                    current_block = p
                elif len(current_block) + 2 + len(p) <= chunk_size and len(current_block) < 150:
                    current_block += "\n\n" + p
                else:
                    chunks.append(current_block)
                    current_block = p
            else:
                if current_block:
                    chunks.append(current_block)
                    current_block = ""
                # Split large paragraph by sentences
                sents = _split_into_sentences(p)
                p_chunk = ""
                for s in sents:
                    if len(s) > chunk_size:
                        if p_chunk:
                            chunks.append(p_chunk)
                            p_chunk = ""
                        chunks.extend(_split_oversized(s, chunk_size, chunk_overlap))
                    else:
                        cand = s if not p_chunk else p_chunk + " " + s
                        if len(cand) <= chunk_size:
                            p_chunk = cand
                        else:
                            if p_chunk:
                                chunks.append(p_chunk)
                            p_chunk = s
                if p_chunk:
                    current_block = p_chunk

        if current_block:
            chunks.append(current_block)
    else:
        # Standard continuous text (single paragraph or plain text)
        sentences = _split_into_sentences(full_text)
        current_chunk = ""

        for s in sentences:
            if len(s) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(_split_oversized(s, chunk_size, chunk_overlap))
            else:
                candidate = s if not current_chunk else current_chunk + " " + s
                if len(candidate) <= chunk_size:
                    current_chunk = candidate
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    # Apply overlap from trailing words of the previous chunk
                    if chunk_overlap > 0 and current_chunk:
                        prev_words = current_chunk.split()
                        overlap_words = []
                        o_len = 0
                        for w in reversed(prev_words):
                            t_len = len(w) if o_len == 0 else o_len + 1 + len(w)
                            if t_len <= chunk_overlap:
                                overlap_words.insert(0, w)
                                o_len = t_len
                            else:
                                break
                        if overlap_words:
                            prefix = " ".join(overlap_words)
                            test_combine = prefix + " " + s
                            if len(test_combine) <= chunk_size:
                                current_chunk = test_combine
                            else:
                                current_chunk = s
                        else:
                            current_chunk = s
                    else:
                        current_chunk = s

        if current_chunk:
            chunks.append(current_chunk)

    # Clean and filter duplicates
    final_chunks = []
    for c in chunks:
        c_clean = c.strip()
        if c_clean and (not final_chunks or final_chunks[-1] != c_clean):
            final_chunks.append(c_clean)

    return final_chunks