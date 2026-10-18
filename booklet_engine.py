
def arrange_booklet(selected_pages):
    """
    Arrange selected source-page indexes for booklet printing.

    selected_pages: zero-based source-page indexes in reading order.
    None represents a blank page.

    Returns a list of sheets, each containing:
    (front_left, front_right, back_left, back_right)
    """
    pages = list(selected_pages)

    if not pages:
        raise ValueError("Select at least one page first.")

    # Add blank pages until the total is divisible by 4.
    while len(pages) % 4 != 0:
        pages.append(None)

    total = len(pages)
    sheets = []

    for i in range(total // 4):
        # Convert the booklet's 1-based positions to Python indexes.
        front_left = pages[total - 1 - 2 * i]
        front_right = pages[2 * i]

        back_left = pages[2 * i + 1]
        back_right = pages[total - 2 - 2 * i]

        sheets.append(
            (front_left, front_right, back_left, back_right)
        )

    return sheets


if __name__ == "__main__":
    result = arrange_booklet(list(range(8)))

    for number, (fl, fr, bl, br) in enumerate(result, start=1):
        print(f"Sheet {number}:")
        print(f"  Front: {fl}, {fr}")
        print(f"  Back:  {bl}, {br}")
