# Changelog


## dev notes

2019-04-28
* Diving into parsing all the different tags that come back from Lich
* Displaying text happens more slowly than I'd like. Is this a problem with buffer access?
* Formalized a way to associate colors with tags, but it doesn't seem like the greatest method

2018-02-26
* Cursor seems like it needs to be moved by the main screen, as a derwin could not move the cursor.
* Errors that occur within a coroutine show up when you exit the program.
* GUI is stable enough to start receiving and formatting game output.

2018-02-25
* Before running, start lich with: `ruby lich.rbw --login <character> --without-frontend --detachable-client=8000`
* Server read and write are commented out
* Window sizes and placement are only to facilitate testing
* asyncio works pretty well for "threading", but it's a bitch to debug-- if there's an error in a coroutine, only that coroutine crashes and doesn't complain. Try logging to file, or somewhere else, with the logging class.
