def diff_product_ids(before: list[str], after: list[str]):
    old=set(before); new=set(after)
    return {"added":sorted(new-old),"removed":sorted(old-new)}
