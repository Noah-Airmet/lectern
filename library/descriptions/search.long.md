Search the library. Each hit is one page of a book, with a url that opens exactly that page; cite that url.

Query grammar: words are ANDed; "a phrase" in double quotes; prefix* (at least 3 letters); a NEAR/5 b; -word excludes. Example: "plurality of gods" Melchizedek -Abraham. There is no OR: run one search per alternative. There is no stemming: baptiz* finds baptize, baptized and baptizing. The text is OCR of old books, so try the period's spellings (shew, connexion, Saviour) and synonyms when a search comes back thin. An empty query lists books that match the filters.

Filters: collection (the shelf: latter-day-saints, church-fathers, bible-texts, bible-study, jewish-antiquity, classics, languages, theology-history, shorthand), org (publisher), date_from and date_to (YYYY, the year the book was printed), doc (one book id, such as jod:01 or npnf2:04-select-works-and-letters, to search inside it). mode="documents" ranks whole books by their hits, for triage. sort="date" puts the latest printed first. limit is 1 to 25; pass next_cursor back as cursor for more.

Snippets are short. Read a hit in full with fetch.
