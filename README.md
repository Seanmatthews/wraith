### dev notes

2018-02-25
* Before running, start lich with: `ruby lich.rbw --login <character> --without-frontend --detachable-client=8000`
* Server read and write are commented out
* Window sizes and placement are only to facilitate testing
* asyncio works pretty well for "threading", but it's a bitch to debug-- if there's an error in a coroutine, only that coroutine crashes and doesn't complain. Try logging to file, or somewhere else, with the logging class.