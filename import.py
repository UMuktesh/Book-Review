from csv import reader
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
import requests

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

f = open("books.csv")
reader = reader(f)
for row in reader:
    if row[3] == 'year':
        continue;
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:i, :t, :a, :y)", {"i":row[0], "t":row[1], "a":row[2], "y":int(row[3])})
db.commit()

    