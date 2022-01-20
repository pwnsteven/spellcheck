import hashlib
import re
import requests
import traceback
import unittest

from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest import mock


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

    # Clean the document of new lines and split on hyphens and spaces
    doc_split_by_word = re.split(' |-', doc_text.replace('\n', ' '))

    # Clean any remaining non-alpha characters from the string (leaving apostrophized words per spec)
    words = []
    for word in doc_split_by_word:
        clean_word = re.sub(r"[^A-Za-z']", "", word)
        if clean_word:
            words.append(clean_word)

    return words


def validate_and_hash(misspelled_words, doc_text):
    """ Utility to format and hash the list of misspelled words

    Since calls were ran in parallel, we need to validate that the misspelled words are sequential

    Arguments:
        misspelled_words: List of misspelled words
        doc_text: The document text
    """

    if not misspelled_words:
        raise Exception(f'No words misspelled words found')

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
    """ Test to showcase API knowledge. Send code to email once it's deciphered.

    1. Retrieve a text document from: https://outside-interview.herokuapp.com/document
    2. Validate the spelling of each `cleaned` word via: https://outside-interview.herokuapp.com/spelling/<word>
    3. Hash (md5) the concatenated misspelled words
    4. Use the lowercase hex digest of the md5 concatenated with @outsideinc.com
    """

    # Store data for reference
    prog_data = {}

    # Create a session for a persistent HTTP connection..
    session = requests.Session()

    try:

        # Grab and store the document
        doc_text = get_document(session)
        prog_data['document'] = doc_text

        # Clean and format the document's text
        clean_words = clean_and_format_document(doc_text)
        word_urls = [f'https://outside-interview.herokuapp.com/spelling/{word}' for word in clean_words]
        prog_data['word_count'] = len(clean_words)

        # Use a pool of threads to exc the various req calls concurrently as we wait for data
        with ThreadPoolExecutor(max_workers=None) as executor:

            word_validation = []
            misspelled_words = []
            future_idx = {executor.submit(request_util, session, url): url for url in word_urls}
            for idx, future in enumerate(as_completed(future_idx), start=1):

                # Strip the word out and check for validation based on the response status
                url = future_idx[future]
                word = url.rsplit("/", 1)[-1]
                spelled_correctly = True

                resp = future.result()
                if resp.status_code == 404:
                    spelled_correctly = False
                    misspelled_words.append(word)

                word_validation.append(f'{idx}/{len(clean_words)}: [{word}] is valid - {spelled_correctly}')

            # Store validation notes to the program data
            prog_data['word_validation'] = word_validation

        session.close()

        prog_data['misspelled_words'] = misspelled_words

        email_address = validate_and_hash(misspelled_words, doc_text)
        prog_data['email_address'] = f'{email_address}@outsideinc.com'

        print(prog_data)
        return prog_data

    except Exception as exc:
        stack = traceback.format_exc()
        print(f'Error occurred: {exc}\n\n{stack}')


# ======================================================================
# Unit Testing
# ----------------------------------------------------------------------
TEST_DOC_TEXT = '\nUnit-testing.\n\nThis is forr the Outside interveiw test!'


def mocked_get_requests(*args, **kwargs):

    class MockResponse:

        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

        def text(self):
            return self.text

    url = args[0]

    # Document endpoint response
    if 'document' in url:
        return MockResponse(200, TEST_DOC_TEXT)

    # Spellcheck response - Return 204 for correct spelling and 404 for incorrect
    else:
        misspells = ['interveiw', 'forr']
        status_code = 204
        res = [ele for ele in misspells if(ele in url)]
        if len(res) != 0:
            status_code = 404

        return MockResponse(status_code, '')


class SpellCheckerUnitTests(unittest.TestCase):

    """
    {
       "document":"\nUnit-testing.\n\nThis is forr the Outside interveiw test!",
       "word_count":9,
       "word_validation":[
          "1/9: [forr] is valid - False",
          "2/9: [Unit] is valid - True",
          "3/9: [This] is valid - True",
          "4/9: [the] is valid - True",
          "5/9: [is] is valid - True",
          "6/9: [testing] is valid - True",
          "7/9: [Outside] is valid - True",
          "8/9: [interveiw] is valid - False",
          "9/9: [test] is valid - True"
       ],
       "misspelled_words":[
          "forr",
          "interveiw"
       ],
       "email_address":"5ffbab63d0296f874bafe4f9bbdd2e73@outsideinc.com"
    }
    """

    @mock.patch('requests.Session.get', side_effect=mocked_get_requests)
    def test_request_util(self, mock_get):

        test_session = requests.Session()

        # Test document
        response = request_util(test_session, 'https://outside-interview.herokuapp.com/document')
        self.assertEqual(response.text, TEST_DOC_TEXT)

        # Test correct spelling
        response = request_util(test_session, 'https://outside-interview.herokuapp.com/spelling/interveiw')
        self.assertEqual(response.status_code, 404)

        # Test misspelled
        response = request_util(test_session, 'https://outside-interview.herokuapp.com/spelling/Outside')
        self.assertEqual(response.status_code, 204)

        # Test the full program
        program_data = get_outside_email()
        self.assertEqual(program_data['document'], "\nUnit-testing.\n\nThis is forr the Outside interveiw test!")
        self.assertEqual(program_data['word_count'], 9)
        self.assertEqual(program_data['misspelled_words'], ['forr', 'interveiw'])
        self.assertEqual(program_data['email_address'], '5ffbab63d0296f874bafe4f9bbdd2e73@outsideinc.com')

    def test_clean_and_format_document(self):
        """ Test the formatting and splitting of the document """

        words = clean_and_format_document(TEST_DOC_TEXT)
        self.assertEqual(words, ['Unit', 'testing', 'This', 'is', 'forr', 'the', 'Outside', 'interveiw', 'test'])

    def test_validate_and_hash(self):
        """ Test the validation and hashing functionality """

        email_address = validate_and_hash(['forr', 'interveiw'], TEST_DOC_TEXT)
        self.assertEqual(email_address, '5ffbab63d0296f874bafe4f9bbdd2e73')

        # This should throw an exception since the misspelled words are out of order
        with self.assertRaises(Exception):
            validate_and_hash(['interview', 'forr'], TEST_DOC_TEXT)


# ======================================================================
# Run Program
# ----------------------------------------------------------------------
if __name__ == '__main__':

    # unittest.main()
    get_outside_email()

    """
    Program output: 
    
    {
       "document":"\nIt\\'s April on the coast of Maine, and I\\'m upside-down underwater again. The ocean\\'s surface is a green gauze curtain swaying in the wind, and I can\\'t tell sideways from up. Think. I force my numb hands to loosen their grip on the paddle and let it float upward, finding the edge of my kayak. I\\'ve run out of air to blow through my nostrils, but I can hold my breath a little longer. Remember the steps.\nInside the cockpit, my knees grip the underside of the deck. My thoughts are frozen sludge, like honey moving to the bottom of an overturned jar. I touch the blade of my paddle to the gunnel, wrench my shivering muscles forward until my nose is nearly touching the deck, and sweep the paddle forward and out, pulling against the surface like it\\'s something solid. I feel half my face touch dry air and gasp, taking in a mouthful of water before I crash down again. Panicking, I abandon the paddle, tear my spray skirt off the combing, and lunge for the surface, kicking my legs free of the boat. Then I\\'m floating, straining against the tight gasket of my drysuit to suck air. Twenty feet from me, snow is erasing the beach.\nIt took me five months to learn to roll a sea kayak dependbaly, and from either side. It took another two before I could do it in surf. The first time I tried was in the warm Pacific waters off Baja, with a NOLS instructor shouting advice from the beach.\n\"Relax, Lunita, you will never get it if you come up too fast!\"\nEvery time I came within reach of the surface, I\\'d jerk my head toward air, twisting my torso and stopping the momentum of the roling boat. Again and again I wet-exited and came up coughing, the salt water searing my eyes and thraot. Three weeks before, on the first day of NOLS\\'s kayaking section, a storm stranded us on the beach. From benaeth the snapping hem of a tarp, I watched as my instructor waded out into the whitecaps, smacked his bow through the confused chop near the shoreline, and began to surf the long, rearing swells as they tumbled and broke. Whenever a wave sent a grappling hook of heavy water over his gunnel, tipping him into the surge of foam, he\\'d roll back up on the other side of the break. I watched the instructor get pushed by the white crest of a wave like a sled gathering speed; it was the most graceful thing I\\'d ever seen.\n",
       "word_count":434,
       "word_validation":[
          "1/434: [April] is valid - True",
          "2/434: [again] is valid - True",
          "3/434: [The] is valid - True",
          "4/434: [coast] is valid - True",
          "5/434: [ocean's] is valid - True",
          "6/434: [Maine] is valid - True",
          "7/434: [and] is valid - True",
          "8/434: [It's] is valid - True",
          "9/434: [upside] is valid - True",
          "10/434: [I'm] is valid - True",
          "11/434: [down] is valid - True",
          "12/434: [underwater] is valid - True",
          "13/434: [on] is valid - True",
          "14/434: [of] is valid - True",
          "15/434: [the] is valid - True",
          "16/434: [in] is valid - True",
          "17/434: [wind] is valid - True",
          "18/434: [I] is valid - True",
          "19/434: [curtain] is valid - True",
          "20/434: [surface] is valid - True",
          "21/434: [and] is valid - True",
          "22/434: [is] is valid - True",
          "23/434: [a] is valid - True",
          "24/434: [swaying] is valid - True",
          "25/434: [green] is valid - True",
          "26/434: [the] is valid - True",
          "27/434: [gauze] is valid - True",
          "28/434: [tell] is valid - True",
          "29/434: [up] is valid - True",
          "30/434: [Think] is valid - True",
          "31/434: [force] is valid - True",
          "32/434: [from] is valid - True",
          "33/434: [my] is valid - True",
          "34/434: [sideways] is valid - True",
          "35/434: [hands] is valid - True",
          "36/434: [I] is valid - True",
          "37/434: [numb] is valid - True",
          "38/434: [to] is valid - True",
          "39/434: [can't] is valid - True",
          "40/434: [loosen] is valid - True",
          "41/434: [their] is valid - True",
          "42/434: [grip] is valid - True",
          "43/434: [on] is valid - True",
          "44/434: [the] is valid - True",
          "45/434: [and] is valid - True",
          "46/434: [paddle] is valid - True",
          "47/434: [it] is valid - True",
          "48/434: [upward] is valid - True",
          "49/434: [let] is valid - True",
          "50/434: [float] is valid - True",
          "51/434: [finding] is valid - True",
          "52/434: [the] is valid - True",
          "53/434: [edge] is valid - True",
          "54/434: [of] is valid - True",
          "55/434: [my] is valid - True",
          "56/434: [kayak] is valid - True",
          "57/434: [I've] is valid - True",
          "58/434: [run] is valid - True",
          "59/434: [of] is valid - True",
          "60/434: [out] is valid - True",
          "61/434: [to] is valid - True",
          "62/434: [blow] is valid - True",
          "63/434: [through] is valid - True",
          "64/434: [air] is valid - True",
          "65/434: [my] is valid - True",
          "66/434: [nostrils] is valid - True",
          "67/434: [but] is valid - True",
          "68/434: [I] is valid - True",
          "69/434: [can] is valid - True",
          "70/434: [hold] is valid - True",
          "71/434: [my] is valid - True",
          "72/434: [breath] is valid - True",
          "73/434: [a] is valid - True",
          "74/434: [little] is valid - True",
          "75/434: [Remember] is valid - True",
          "76/434: [longer] is valid - True",
          "77/434: [steps] is valid - True",
          "78/434: [the] is valid - True",
          "79/434: [Inside] is valid - True",
          "80/434: [the] is valid - True",
          "81/434: [cockpit] is valid - True",
          "82/434: [my] is valid - True",
          "83/434: [knees] is valid - True",
          "84/434: [grip] is valid - True",
          "85/434: [the] is valid - True",
          "86/434: [of] is valid - True",
          "87/434: [underside] is valid - True",
          "88/434: [the] is valid - True",
          "89/434: [deck] is valid - True",
          "90/434: [My] is valid - True",
          "91/434: [thoughts] is valid - True",
          "92/434: [are] is valid - True",
          "93/434: [frozen] is valid - True",
          "94/434: [sludge] is valid - True",
          "95/434: [like] is valid - True",
          "96/434: [honey] is valid - True",
          "97/434: [moving] is valid - True",
          "98/434: [to] is valid - True",
          "99/434: [bottom] is valid - True",
          "100/434: [the] is valid - True",
          "101/434: [of] is valid - True",
          "102/434: [an] is valid - True",
          "103/434: [overturned] is valid - True",
          "104/434: [jar] is valid - True",
          "105/434: [I] is valid - True",
          "106/434: [touch] is valid - True",
          "107/434: [the] is valid - True",
          "108/434: [blade] is valid - True",
          "109/434: [of] is valid - True",
          "110/434: [my] is valid - True",
          "111/434: [paddle] is valid - True",
          "112/434: [the] is valid - True",
          "113/434: [to] is valid - True",
          "114/434: [gunnel] is valid - True",
          "115/434: [my] is valid - True",
          "116/434: [wrench] is valid - True",
          "117/434: [shivering] is valid - True",
          "118/434: [muscles] is valid - True",
          "119/434: [forward] is valid - True",
          "120/434: [until] is valid - True",
          "121/434: [my] is valid - True",
          "122/434: [nose] is valid - True",
          "123/434: [is] is valid - True",
          "124/434: [nearly] is valid - True",
          "125/434: [touching] is valid - True",
          "126/434: [the] is valid - True",
          "127/434: [deck] is valid - True",
          "128/434: [and] is valid - True",
          "129/434: [sweep] is valid - True",
          "130/434: [the] is valid - True",
          "131/434: [paddle] is valid - True",
          "132/434: [and] is valid - True",
          "133/434: [forward] is valid - True",
          "134/434: [out] is valid - True",
          "135/434: [pulling] is valid - True",
          "136/434: [against] is valid - True",
          "137/434: [the] is valid - True",
          "138/434: [surface] is valid - True",
          "139/434: [it's] is valid - True",
          "140/434: [like] is valid - True",
          "141/434: [something] is valid - True",
          "142/434: [solid] is valid - True",
          "143/434: [I] is valid - True",
          "144/434: [half] is valid - True",
          "145/434: [feel] is valid - True",
          "146/434: [my] is valid - True",
          "147/434: [face] is valid - True",
          "148/434: [touch] is valid - True",
          "149/434: [dry] is valid - True",
          "150/434: [air] is valid - True",
          "151/434: [and] is valid - True",
          "152/434: [taking] is valid - True",
          "153/434: [gasp] is valid - True",
          "154/434: [a] is valid - True",
          "155/434: [in] is valid - True",
          "156/434: [mouthful] is valid - True",
          "157/434: [of] is valid - True",
          "158/434: [before] is valid - True",
          "159/434: [water] is valid - True",
          "160/434: [I] is valid - True",
          "161/434: [crash] is valid - True",
          "162/434: [down] is valid - True",
          "163/434: [again] is valid - True",
          "164/434: [Panicking] is valid - True",
          "165/434: [I] is valid - True",
          "166/434: [abandon] is valid - True",
          "167/434: [the] is valid - True",
          "168/434: [paddle] is valid - True",
          "169/434: [tear] is valid - True",
          "170/434: [spray] is valid - True",
          "171/434: [my] is valid - True",
          "172/434: [the] is valid - True",
          "173/434: [skirt] is valid - True",
          "174/434: [combing] is valid - True",
          "175/434: [off] is valid - True",
          "176/434: [and] is valid - True",
          "177/434: [lunge] is valid - True",
          "178/434: [the] is valid - True",
          "179/434: [for] is valid - True",
          "180/434: [surface] is valid - True",
          "181/434: [kicking] is valid - True",
          "182/434: [my] is valid - True",
          "183/434: [legs] is valid - True",
          "184/434: [free] is valid - True",
          "185/434: [of] is valid - True",
          "186/434: [the] is valid - True",
          "187/434: [boat] is valid - True",
          "188/434: [Then] is valid - True",
          "189/434: [I'm] is valid - True",
          "190/434: [straining] is valid - True",
          "191/434: [floating] is valid - True",
          "192/434: [the] is valid - True",
          "193/434: [against] is valid - True",
          "194/434: [tight] is valid - True",
          "195/434: [gasket] is valid - True",
          "196/434: [my] is valid - True",
          "197/434: [of] is valid - True",
          "198/434: [drysuit] is valid - True",
          "199/434: [to] is valid - True",
          "200/434: [suck] is valid - True",
          "201/434: [air] is valid - True",
          "202/434: [Twenty] is valid - True",
          "203/434: [from] is valid - True",
          "204/434: [feet] is valid - True",
          "205/434: [snow] is valid - True",
          "206/434: [me] is valid - True",
          "207/434: [erasing] is valid - True",
          "208/434: [is] is valid - True",
          "209/434: [the] is valid - True",
          "210/434: [took] is valid - True",
          "211/434: [It] is valid - True",
          "212/434: [beach] is valid - True",
          "213/434: [five] is valid - True",
          "214/434: [me] is valid - True",
          "215/434: [months] is valid - True",
          "216/434: [to] is valid - True",
          "217/434: [to] is valid - True",
          "218/434: [learn] is valid - True",
          "219/434: [roll] is valid - True",
          "220/434: [sea] is valid - True",
          "221/434: [dependbaly] is valid - True",
          "222/434: [kayak] is valid - True",
          "223/434: [and] is valid - True",
          "224/434: [a] is valid - True",
          "225/434: [from] is valid - True",
          "226/434: [either] is valid - True",
          "227/434: [side] is valid - True",
          "228/434: [It] is valid - True",
          "229/434: [took] is valid - True",
          "230/434: [another] is valid - True",
          "231/434: [two] is valid - True",
          "232/434: [before] is valid - True",
          "233/434: [could] is valid - True",
          "234/434: [I] is valid - True",
          "235/434: [do] is valid - True",
          "236/434: [in] is valid - True",
          "237/434: [surf] is valid - True",
          "238/434: [it] is valid - True",
          "239/434: [The] is valid - True",
          "240/434: [first] is valid - True",
          "241/434: [time] is valid - True",
          "242/434: [I] is valid - True",
          "243/434: [tried] is valid - True",
          "244/434: [was] is valid - True",
          "245/434: [in] is valid - True",
          "246/434: [the] is valid - True",
          "247/434: [warm] is valid - True",
          "248/434: [Pacific] is valid - True",
          "249/434: [off] is valid - True",
          "250/434: [waters] is valid - True",
          "251/434: [with] is valid - True",
          "252/434: [Baja] is valid - True",
          "253/434: [a] is valid - True",
          "254/434: [NOLS] is valid - False",
          "255/434: [instructor] is valid - True",
          "256/434: [shouting] is valid - True",
          "257/434: [advice] is valid - True",
          "258/434: [from] is valid - True",
          "259/434: [the] is valid - True",
          "260/434: [beach] is valid - True",
          "261/434: [Relax] is valid - True",
          "262/434: [you] is valid - True",
          "263/434: [Lunita] is valid - True",
          "264/434: [will] is valid - True",
          "265/434: [never] is valid - True",
          "266/434: [get] is valid - True",
          "267/434: [if] is valid - True",
          "268/434: [you] is valid - True",
          "269/434: [it] is valid - True",
          "270/434: [come] is valid - True",
          "271/434: [up] is valid - True",
          "272/434: [too] is valid - True",
          "273/434: [fast] is valid - True",
          "274/434: [Every] is valid - True",
          "275/434: [I] is valid - True",
          "276/434: [time] is valid - True",
          "277/434: [came] is valid - True",
          "278/434: [within] is valid - True",
          "279/434: [reach] is valid - True",
          "280/434: [of] is valid - True",
          "281/434: [the] is valid - True",
          "282/434: [surface] is valid - True",
          "283/434: [I'd] is valid - True",
          "284/434: [jerk] is valid - True",
          "285/434: [my] is valid - True",
          "286/434: [toward] is valid - True",
          "287/434: [air] is valid - True",
          "288/434: [head] is valid - True",
          "289/434: [twisting] is valid - True",
          "290/434: [my] is valid - True",
          "291/434: [torso] is valid - True",
          "292/434: [and] is valid - True",
          "293/434: [stopping] is valid - True",
          "294/434: [the] is valid - True",
          "295/434: [momentum] is valid - True",
          "296/434: [of] is valid - True",
          "297/434: [the] is valid - True",
          "298/434: [roling] is valid - False",
          "299/434: [Again] is valid - True",
          "300/434: [and] is valid - True",
          "301/434: [boat] is valid - True",
          "302/434: [again] is valid - True",
          "303/434: [I] is valid - True",
          "304/434: [wet] is valid - True",
          "305/434: [exited] is valid - True",
          "306/434: [and] is valid - True",
          "307/434: [came] is valid - True",
          "308/434: [up] is valid - True",
          "309/434: [the] is valid - True",
          "310/434: [coughing] is valid - True",
          "311/434: [salt] is valid - True",
          "312/434: [water] is valid - True",
          "313/434: [searing] is valid - True",
          "314/434: [my] is valid - True",
          "315/434: [eyes] is valid - True",
          "316/434: [and] is valid - True",
          "317/434: [thraot] is valid - False",
          "318/434: [Three] is valid - True",
          "319/434: [weeks] is valid - True",
          "320/434: [before] is valid - True",
          "321/434: [on] is valid - True",
          "322/434: [the] is valid - True",
          "323/434: [first] is valid - True",
          "324/434: [day] is valid - True",
          "325/434: [of] is valid - True",
          "326/434: [NOLS's] is valid - False",
          "327/434: [kayaking] is valid - True",
          "328/434: [section] is valid - True",
          "329/434: [a] is valid - True",
          "330/434: [storm] is valid - True",
          "331/434: [stranded] is valid - True",
          "332/434: [us] is valid - True",
          "333/434: [on] is valid - True",
          "334/434: [the] is valid - True",
          "335/434: [beach] is valid - True",
          "336/434: [benaeth] is valid - False",
          "337/434: [From] is valid - True",
          "338/434: [the] is valid - True",
          "339/434: [snapping] is valid - True",
          "340/434: [hem] is valid - True",
          "341/434: [of] is valid - True",
          "342/434: [a] is valid - True",
          "343/434: [tarp] is valid - True",
          "344/434: [I] is valid - True",
          "345/434: [watched] is valid - True",
          "346/434: [my] is valid - True",
          "347/434: [as] is valid - True",
          "348/434: [instructor] is valid - True",
          "349/434: [out] is valid - True",
          "350/434: [into] is valid - True",
          "351/434: [the] is valid - True",
          "352/434: [waded] is valid - True",
          "353/434: [whitecaps] is valid - True",
          "354/434: [smacked] is valid - True",
          "355/434: [his] is valid - True",
          "356/434: [bow] is valid - True",
          "357/434: [through] is valid - True",
          "358/434: [the] is valid - True",
          "359/434: [chop] is valid - True",
          "360/434: [near] is valid - True",
          "361/434: [confused] is valid - True",
          "362/434: [the] is valid - True",
          "363/434: [shoreline] is valid - True",
          "364/434: [and] is valid - True",
          "365/434: [began] is valid - True",
          "366/434: [surf] is valid - True",
          "367/434: [to] is valid - True",
          "368/434: [the] is valid - True",
          "369/434: [long] is valid - True",
          "370/434: [rearing] is valid - True",
          "371/434: [swells] is valid - True",
          "372/434: [as] is valid - True",
          "373/434: [they] is valid - True",
          "374/434: [and] is valid - True",
          "375/434: [Whenever] is valid - True",
          "376/434: [broke] is valid - True",
          "377/434: [tumbled] is valid - True",
          "378/434: [wave] is valid - True",
          "379/434: [a] is valid - True",
          "380/434: [sent] is valid - True",
          "381/434: [grappling] is valid - True",
          "382/434: [hook] is valid - True",
          "383/434: [of] is valid - True",
          "384/434: [heavy] is valid - True",
          "385/434: [water] is valid - True",
          "386/434: [over] is valid - True",
          "387/434: [gunnel] is valid - True",
          "388/434: [his] is valid - True",
          "389/434: [him] is valid - True",
          "390/434: [into] is valid - True",
          "391/434: [tipping] is valid - True",
          "392/434: [the] is valid - True",
          "393/434: [surge] is valid - True",
          "394/434: [of] is valid - True",
          "395/434: [foam] is valid - True",
          "396/434: [roll] is valid - True",
          "397/434: [he'd] is valid - True",
          "398/434: [back] is valid - True",
          "399/434: [up] is valid - True",
          "400/434: [on] is valid - True",
          "401/434: [the] is valid - True",
          "402/434: [other] is valid - True",
          "403/434: [side] is valid - True",
          "404/434: [of] is valid - True",
          "405/434: [the] is valid - True",
          "406/434: [a] is valid - True",
          "407/434: [break] is valid - True",
          "408/434: [I] is valid - True",
          "409/434: [watched] is valid - True",
          "410/434: [the] is valid - True",
          "411/434: [get] is valid - True",
          "412/434: [instructor] is valid - True",
          "413/434: [pushed] is valid - True",
          "414/434: [by] is valid - True",
          "415/434: [the] is valid - True",
          "416/434: [white] is valid - True",
          "417/434: [crest] is valid - True",
          "418/434: [of] is valid - True",
          "419/434: [a] is valid - True",
          "420/434: [wave] is valid - True",
          "421/434: [like] is valid - True",
          "422/434: [gathering] is valid - True",
          "423/434: [a] is valid - True",
          "424/434: [speed] is valid - True",
          "425/434: [sled] is valid - True",
          "426/434: [it] is valid - True",
          "427/434: [was] is valid - True",
          "428/434: [the] is valid - True",
          "429/434: [most] is valid - True",
          "430/434: [graceful] is valid - True",
          "431/434: [thing] is valid - True",
          "432/434: [ever] is valid - True",
          "433/434: [I'd] is valid - True",
          "434/434: [seen] is valid - True"
       ],
       "misspelled_words":[
          "NOLS",
          "roling",
          "thraot",
          "NOLS's",
          "benaeth"
       ],
       "email_address":"734c497e6d014b043dd961b6c4f472d1@outsideinc.com"
    }
    """