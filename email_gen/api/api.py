import hashlib
import re
import requests
import traceback
import unittest

from concurrent.futures import ThreadPoolExecutor, as_completed


def request_util(session, url):
    """ A request utility to use across the program

    Arguments:
        session: The Session object
        url: The url
    """

    try:
        response = session.get(url, timeout=3)
        return response
    except Exception:
        raise


def get_document(session):
    """ Document getter

    Argument:
        session: The Session object
    """
    response = request_util(session, 'https://outside-interview.herokuapp.com/document')
    status = response.status_code
    if status != 200:
        error = f'Received an HTTP {status} when attempting to retrieve the document'
        raise Exception(error)

    return response.text


def clean_and_format_document(doc_text):
    """ Clean the words in the provided document and format them in a list to be validated.

    Clean: Remove all non-alpha characters (eg. commas, periods, exclamations, etc.) and line breaks
    Format: Create a list of all words, breaking them at spaces and hyphens
    """

    doc_split_by_word = re.split(' |-', doc_text.replace('\n', ' '))

    words = []
    for word in doc_split_by_word:
        clean_word = re.sub(r"[^A-Za-z']", "", word)
        if clean_word:  # Remove empty entries
            words.append(clean_word)

    return words


def validate_and_hash(misspelled_words, doc_text):
    """ Utility to format and hash the list of misspelled words

    Arguments:
        misspelled_words: List of misspelled words
        doc_text: The document text
    """

    if not misspelled_words:
        raise Exception(f'No words misspelled words found')

    # Since calls are ran in parallel, we need to validate that the misspelled words are sequential
    doc_idx = 0
    for word in misspelled_words:
        idx = doc_text.find(word)
        if idx < doc_idx:
            raise Exception(f'Misspelled words are out of alignment. Need to re-verify')
        doc_idx = idx

    hash_this = ''.join(misspelled_words)
    hash_obj = hashlib.md5(hash_this.encode())
    email_address = hash_obj.hexdigest().lower()

    return email_address


def get_outside_email():

    session = requests.Session()

    try:

        doc_text = get_document(session)
        clean_words = clean_and_format_document(doc_text)
        word_urls = [f'https://outside-interview.herokuapp.com/spelling/{word}' for word in clean_words]

        with ThreadPoolExecutor(max_workers=None) as executor:

            misspelled_words = []
            future_idx = {executor.submit(request_util, session, url): url for url in word_urls}
            for future in as_completed(future_idx):

                # Validate, grab and store the word if a 404 is returned...
                url = future_idx[future]
                word = url.rsplit("/", 1)[-1]

                resp = future.result()
                if resp.status_code == 404:
                    misspelled_words.append(word)

        session.close()

        email_address = validate_and_hash(misspelled_words)
        print(email_address)

    except Exception as exc:

        # Provide stacktrace for any errors
        stack = traceback.format_stack()
        print(f'Error occurred - {exc}\n\n{stack}')


# ======================================================================
# Unit Testing
# ----------------------------------------------------------------------
TEST_DOC_TEXT = '\nUnit-testing.\n\nThis is forr the Outside interveiw test!'


class SpellCheckerUnitTests(unittest.TestCase):

    def test_clean_and_format_document(self):

        # Test to see if we split the words correctly based on the regex patterns and formatting logic
        words = clean_and_format_document(TEST_DOC_TEXT)
        self.assertEqual(words, ['Unit', 'testing', 'This', 'is', 'forr', 'the', 'Outside', 'interveiw', 'test'])

    def test_validate_and_hash(self):

        email_address = validate_and_hash(['forr', 'interveiw'], TEST_DOC_TEXT)
        self.assertEqual(email_address, '5ffbab63d0296f874bafe4f9bbdd2e73')

        # then out of order...
        with self.assertRaises(Exception):
            validate_and_hash(['interview', 'forr'], TEST_DOC_TEXT)


if __name__ == '__main__':

    """ Util unit tests passing fwiw: 
    
    /home/steven/spellcheck/ve/bin/python /home/steven/spellcheck/email_gen/api/api.py
    ..
    ----------------------------------------------------------------------
    Ran 2 tests in 0.000s
    
    OK
    """

    unittest.main()

    # get_outside_email()
