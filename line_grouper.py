def get_left(word):
    return min(point[0] for point in word["bbox"])


def get_right(word):
    return max(point[0] for point in word["bbox"])


def get_top(word):
    return min(point[1] for point in word["bbox"])


def get_bottom(word):
    return max(point[1] for point in word["bbox"])


def get_center_x(word):
    return (get_left(word) + get_right(word)) / 2


def vertical_overlap(word1, word2):

    top = max(get_top(word1), get_top(word2))
    bottom = min(get_bottom(word1), get_bottom(word2))

    overlap = bottom - top

    if overlap <= 0:
        return 0

    h1 = get_bottom(word1) - get_top(word1)
    h2 = get_bottom(word2) - get_top(word2)

    return overlap / min(h1, h2)


def group_into_lines(words, overlap_threshold=0.45):

    if not words:
        return []

    words = sorted(
        words,
        key=lambda w: (
            get_top(w),
            get_left(w)
        )
    )

    lines = []

    for word in words:

        added = False

        for line in lines:

            overlaps = [
                vertical_overlap(word, existing)
                for existing in line
            ]

            if max(overlaps) >= overlap_threshold:

                line.append(word)

                added = True
                break

        if not added:
            lines.append([word])

    return lines


def lines_to_text(lines):

    output = []

    for line in lines:

        line = sorted(
            line,
            key=get_left
        )

        sentence = " ".join(
            word["text"]
            for word in line
        )

        confidence = round(
            sum(word["confidence"] for word in line)
            / len(line),
            3
        )

        output.append(
            {
                "text": sentence,
                "confidence": confidence
            }
        )

    return output