import argparse
from file_organizer import load_categories, save_categories


def list_categories(_):
    """Print all categories and their keywords."""
    categories = load_categories()
    for category, keywords in categories.items():
        print(f"{category}: {', '.join(keywords)}")


def add_category(args):
    """Add a new category or keywords to an existing category."""
    categories = load_categories()
    cat = args.category.lower()
    keywords = [k.lower() for k in args.keywords]

    if cat in categories:
        existing = set(categories[cat])
        categories[cat].extend([k for k in keywords if k not in existing])
    else:
        categories[cat] = keywords

    save_categories(categories)
    print(f"Category '{cat}' updated.")


def remove_category(args):
    """Remove keywords from a category or delete the category."""
    categories = load_categories()
    cat = args.category.lower()

    if cat not in categories:
        print(f"Category '{cat}' not found.")
        return

    if args.keywords:
        keywords_to_remove = {k.lower() for k in args.keywords}
        categories[cat] = [k for k in categories[cat] if k not in keywords_to_remove]
        if categories[cat]:
            print(f"Updated category '{cat}'.")
        else:
            del categories[cat]
            print(f"Category '{cat}' removed.")
    else:
        del categories[cat]
        print(f"Category '{cat}' removed.")

    save_categories(categories)


def main():
    parser = argparse.ArgumentParser(description="Manage categories in categories.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_add = subparsers.add_parser("add", help="Add a category or keywords")
    parser_add.add_argument("category", help="Category name")
    parser_add.add_argument("keywords", nargs="*", help="Keywords for the category")
    parser_add.set_defaults(func=add_category)

    parser_remove = subparsers.add_parser("remove", help="Remove a category or keywords")
    parser_remove.add_argument("category", help="Category name")
    parser_remove.add_argument("keywords", nargs="*", help="Keywords to remove")
    parser_remove.set_defaults(func=remove_category)

    parser_list = subparsers.add_parser("list", help="List all categories")
    parser_list.set_defaults(func=list_categories)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
