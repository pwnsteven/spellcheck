import re
import requests
import traceback

from concurrent.futures import ThreadPoolExecutor, as_completed


def request_util(session, url):
    try:
        response = session.get(url)
        return response
    except Exception:
        raise


def get_document(session):
    response = request_util(session, 'https://outside-interview.herokuapp.com/document')
    status = response.status_code
    if status != 200:
        error = f'Received an HTTP {status} when attempting to retrieve the document'
        raise Exception(error)

    return response.text


def clean_and_format_document(doc_text):

    # Split hyphens and spaces
    doc_split_by_word = re.split(' |-', doc_text.replace('\n', ' '))

    # Remove garbage, but keep apostrophized words
    words = []
    for word in doc_split_by_word:
        clean_word = re.sub(r"[^A-Za-z']", "", word)
        if clean_word:
            words.append(clean_word)

    return words


def get_outside_email():

    session = requests.Session()

    try:

        # try and use new util
        doc_text = get_document(session)
        clean_words = clean_and_format_document(doc_text)
        # returned: ["It's", 'April', 'on', 'the', 'coast', 'of', 'Maine', 'and', "I'm", 'upside', 'down', 'underwater', 'again', 'The', "ocean's", 'surface', 'is', 'a', 'green', 'gauze', 'curtain', 'swaying', 'in', 'the', 'wind', 'and', 'I', "can't", 'tell', 'sideways', 'from', 'up', 'Think', 'I', 'force', 'my', 'numb', 'hands', 'to', 'loosen', 'their', 'grip', 'on', 'the', 'paddle', 'and', 'let', 'it', 'float', 'upward', 'finding', 'the', 'edge', 'of', 'my', 'kayak', "I've", 'run', 'out', 'of', 'air', 'to', 'blow', 'through', 'my', 'nostrils', 'but', 'I', 'can', 'hold', 'my', 'breath', 'a', 'little', 'longer', 'Remember', 'the', 'steps', 'Inside', 'the', 'cockpit', 'my', 'knees', 'grip', 'the', 'underside', 'of', 'the', 'deck', 'My', 'thoughts', 'are', 'frozen', 'sludge', 'like', 'honey', 'moving', 'to', 'the', 'bottom', 'of', 'an', 'overturned', 'jar', 'I', 'touch', 'the', 'blade', 'of', 'my', 'paddle', 'to', 'the', 'gunnel', 'wrench', 'my', 'shivering', 'muscles', 'forward', 'until', 'my', 'nose', 'is', 'nearly', 'touching', 'the', 'deck', 'and', 'sweep', 'the', 'paddle', 'forward', 'and', 'out', 'pulling', 'against', 'the', 'surface', 'like', "it's", 'something', 'solid', 'I', 'feel', 'half', 'my', 'face', 'touch', 'dry', 'air', 'and', 'gasp', 'taking', 'in', 'a', 'mouthful', 'of', 'water', 'before', 'I', 'crash', 'down', 'again', 'Panicking', 'I', 'abandon', 'the', 'paddle', 'tear', 'my', 'spray', 'skirt', 'off', 'the', 'combing', 'and', 'lunge', 'for', 'the', 'surface', 'kicking', 'my', 'legs', 'free', 'of', 'the', 'boat', 'Then', "I'm", 'floating', 'straining', 'against', 'the', 'tight', 'gasket', 'of', 'my', 'drysuit', 'to', 'suck', 'air', 'Twenty', 'feet', 'from', 'me', 'snow', 'is', 'erasing', 'the', 'beach', 'It', 'took', 'me', 'five', 'months', 'to', 'learn', 'to', 'roll', 'a', 'sea', 'kayak', 'dependbaly', 'and', 'from', 'either', 'side', 'It', 'took', 'another', 'two', 'before', 'I', 'could', 'do', 'it', 'in', 'surf', 'The', 'first', 'time', 'I', 'tried', 'was', 'in', 'the', 'warm', 'Pacific', 'waters', 'off', 'Baja', 'with', 'a', 'NOLS', 'instructor', 'shouting', 'advice', 'from', 'the', 'beach', 'Relax', 'Lunita', 'you', 'will', 'never', 'get', 'it', 'if', 'you', 'come', 'up', 'too', 'fast', 'Every', 'time', 'I', 'came', 'within', 'reach', 'of', 'the', 'surface', "I'd", 'jerk', 'my', 'head', 'toward', 'air', 'twisting', 'my', 'torso', 'and', 'stopping', 'the', 'momentum', 'of', 'the', 'roling', 'boat', 'Again', 'and', 'again', 'I', 'wet', 'exited', 'and', 'came', 'up', 'coughing', 'the', 'salt', 'water', 'searing', 'my', 'eyes', 'and', 'thraot', 'Three', 'weeks', 'before', 'on', 'the', 'first', 'day', 'of', "NOLS's", 'kayaking', 'section', 'a', 'storm', 'stranded', 'us', 'on', 'the', 'beach', 'From', 'benaeth', 'the', 'snapping', 'hem', 'of', 'a', 'tarp', 'I', 'watched', 'as', 'my', 'instructor', 'waded', 'out', 'into', 'the', 'whitecaps', 'smacked', 'his', 'bow', 'through', 'the', 'confused', 'chop', 'near', 'the', 'shoreline', 'and', 'began', 'to', 'surf', 'the', 'long', 'rearing', 'swells', 'as', 'they', 'tumbled', 'and', 'broke', 'Whenever', 'a', 'wave', 'sent', 'a', 'grappling', 'hook', 'of', 'heavy', 'water', 'over', 'his', 'gunnel', 'tipping', 'him', 'into', 'the', 'surge', 'of', 'foam', "he'd", 'roll', 'back', 'up', 'on', 'the', 'other', 'side', 'of', 'the', 'break', 'I', 'watched', 'the', 'instructor', 'get', 'pushed', 'by', 'the', 'white', 'crest', 'of', 'a', 'wave', 'like', 'a', 'sled', 'gathering', 'speed', 'it', 'was', 'the', 'most', 'graceful', 'thing', "I'd", 'ever', 'seen']

        # Concatenate the spellchecker url to each word to simply make calls over iteration??
        word_urls = [f'https://outside-interview.herokuapp.com/spelling/{word}' for word in clean_words]

        # Use a pool of threads to exc the various req calls concurrently as we wait for data
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

        print(misspelled_words)
        # ['NOLS', 'roling', 'thraot', "NOLS's", 'benaeth'] <------ This is what needs to be concatenated & hashed!!

    except Exception as exc:

        # Provide stacktrace for any errors
        stack = traceback.format_stack()
        print(f'Error occurred - {exc}\n\n{stack}')


if __name__ == '__main__':

    get_outside_email()
