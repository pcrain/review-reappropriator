###

Dependencies:
  PHP (tested with 7.2.13)
  Node.js (tested with 11.3.0) (only needed if you want to run the review scraper yourself)
    google-play-scraper - for downloading review / app data from the Google Play Store
      https://github.com/facundoolano/google-play-scraper
  Python (tested with 3.6.0 and 3.7.1:
    sortedcontainers    - for various indexed data structures with low memory overhead
      http://www.grantjenks.com/docs/sortedcontainers/
    spacy               - for part of speech tagging and various NLP operations
      https://spacy.io/
      * Also need the "en_core_web_sm" data set: https://spacy.io/models/en
    nltk                - for ngram extraction and various NLP operations
      https://www.nltk.org/
    jsonstreamer        - for reading in, parsing, and working with large JSON files
      https://github.com/kashifrazzaqui/json-streamer

Usage Steps:
  - Make sure all dependenices are installed
  - Clone this project from GitHub
  - Download all the files from the following link and put them in the "data" subdirectory
    https://app.box.com/s/dyt062sr3yq8p7xp1if3na9m2vpbpm35
    * These files may be generated manually, but will take a very long time; downloading is recommmended
  - Run "./_launch_server" in an open terminal window
    - Alternately, start the server manually by running "php -S 127.0.0.1:8888" in the project directory
  - In another terminal, run "./0-pipeline"
    * If you are using the files downloaded above, the script may be run as is
    * Otherwise, uncomment all commented commands in the file first before running (they may be safely commented out again after running the first time)
  - Wait for the program data to load into memory. *This will take about 15-30 minutes depending on your machine.*
  - Once loaded, open "6-ui-prototype.html" in a web browser
  - You're ready to go!
