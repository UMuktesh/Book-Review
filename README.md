# Book Review

This website is a Book Review site built on Flask framework where users can create account, view goodreads data for a book and give review and rating to it. API route for JSON data also present.

## Dependencies

- Set a environment variable DATABASE_URL for the Database URL
- Run: pip install -r requirements.txt

## Features

- Create an account.
- Case insensitive Search with validation.
- _/book/isbn_ route for viewing directly a book based on ISBN number.
- _/api/isbn_ for getting JSON data about a book based on ISBN number.
- A one time Rating and Review can be given.