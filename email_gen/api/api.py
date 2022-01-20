import requests
import traceback


def get_outside_email():

    session = requests.Session()

    try:

        # Ping the api...
        doc_url = 'https://outside-interview.herokuapp.com/document'
        print(f'getting document from url..')
        res = session.get(doc_url)
        print(res.status_code)
        print(res.text)

        """
        
        It's April on the coast of Maine, and I'm upside-down underwater again. The ocean's surface is a green gauze curtain swaying in the wind, and I can't tell sideways from up. Think. I force my numb hands to loosen their grip on the paddle and let it float upward, finding the edge of my kayak. I've run out of air to blow through my nostrils, but I can hold my breath a little longer. Remember the steps.
        Inside the cockpit, my knees grip the underside of the deck. My thoughts are frozen sludge, like honey moving to the bottom of an overturned jar. I touch the blade of my paddle to the gunnel, wrench my shivering muscles forward until my nose is nearly touching the deck, and sweep the paddle forward and out, pulling against the surface like it's something solid. I feel half my face touch dry air and gasp, taking in a mouthful of water before I crash down again. Panicking, I abandon the paddle, tear my spray skirt off the combing, and lunge for the surface, kicking my legs free of the boat. Then I'm floating, straining against the tight gasket of my drysuit to suck air. Twenty feet from me, snow is erasing the beach.
        It took me five months to learn to roll a sea kayak dependbaly, and from either side. It took another two before I could do it in surf. The first time I tried was in the warm Pacific waters off Baja, with a NOLS instructor shouting advice from the beach.
        "Relax, Lunita, you will never get it if you come up too fast!"
        Every time I came within reach of the surface, I'd jerk my head toward air, twisting my torso and stopping the momentum of the roling boat. Again and again I wet-exited and came up coughing, the salt water searing my eyes and thraot. Three weeks before, on the first day of NOLS's kayaking section, a storm stranded us on the beach. From benaeth the snapping hem of a tarp, I watched as my instructor waded out into the whitecaps, smacked his bow through the confused chop near the shoreline, and began to surf the long, rearing swells as they tumbled and broke. Whenever a wave sent a grappling hook of heavy water over his gunnel, tipping him into the surge of foam, he'd roll back up on the other side of the break. I watched the instructor get pushed by the white crest of a wave like a sled gathering speed; it was the most graceful thing I'd ever seen.
        """

    except Exception as exc:

        # Provide stacktrace for any errors
        stack = traceback.format_stack()
        print(f'Error occurred - {exc}\n\n{stack}')


if __name__ == '__main__':

    get_outside_email()
