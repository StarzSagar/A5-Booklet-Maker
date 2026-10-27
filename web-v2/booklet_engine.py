def arrange_booklet(selected_pages):
    """Arrange zero-based source page indexes into booklet sheet sides."""
    pages = list(selected_pages)

    if not pages:
        raise ValueError("Select at least one page first.")

    while len(pages) % 4:
        pages.append(None)

    total = len(pages)
    sheets = []

    for index in range(total // 4):
        front_left = pages[total - 1 - 2 * index]
        front_right = pages[2 * index]
        back_left = pages[2 * index + 1]
        back_right = pages[total - 2 - 2 * index]
        sheets.append((front_left, front_right, back_left, back_right))

    return sheets
