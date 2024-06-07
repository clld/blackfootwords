# Running the blackfootwords clld app

1. Clone the repository https://github.com/clld/blackfootwords
2. Activate a virtualenv, install the app:
   ```shell
   pip install -e .
   ```
3. Install `pycldf` and `waitress`:
   ```shell
   pip install waitress
   pip install pycldf
   ```
4. Create the database, i.e. load the CLDF dataset into a db suitable for the web app:
   ```shell
   clld initdb development.ini --cldf PATH/TO/blackfootwords/cldf/Wordlist-metadata.json
   ```
5. Start the app:
   ```shell
   pserve development.ini
   ```

You should now be able to visit the app with your browser at http://localhost:6543/

