import json
from config import DEFAULT_TEXT_MODEL, STORY_MODEL


def generate_idea(client):

    prompt = """
    Generate ONE idea for a YouTube horror-story compilation.

    The channel publishes original fictional horror stories written
    to feel like believable experiences told by real people.

    The video should contain between 7 and 12 stories.

    The concept should be strong enough to create a clickable
    YouTube title while also being broad enough to support
    meaningfully different stories.

    GOOD THEMES allow stories involving different:
    - locations
    - characters
    - threats
    - situations
    - technologies
    - environments
    - explanations
    - endings

    Prefer themes based around an EXPERIENCE, FEELING, SITUATION,
    TIME, or GENERAL TYPE OF ENCOUNTER.

    Examples of the LEVEL OF BREADTH we want:

    - disturbing experiences while alone
    - encounters that became increasingly strange
    - normal nights that suddenly became terrifying
    - situations where someone realized something was wrong
    - unsettling experiences that were never fully explained
    - encounters with strangers that became disturbing
    - creepy experiences involving technology
    - disturbing things people noticed too late

    These are examples of breadth only.
    Do NOT copy these titles.

    Avoid concepts that force nearly every story to have the same
    plot.

    For example, avoid making every video concept about:
    - someone secretly living in a house
    - finding an intruder inside
    - discovering a hidden room
    - being followed home
    - hearing something in the walls
    - finding someone under a bed
    - one extremely specific type of event

    HOWEVER:

    Specific themes are allowed occasionally if they naturally
    support many genuinely different stories.

    The title should:
    - sound clickable without being ridiculous
    - clearly communicate that the video contains scary stories
    - sound natural on YouTube
    - avoid excessive clickbait
    - accurately represent the topic
    - include the number of stories
    - preferably be easy to understand immediately

    The topic description should explain what kinds of stories
    belong in the compilation without forcing every story to follow
    the same structure.

    Return ONLY valid JSON using exactly this structure:

    {
        "title": "video title",
        "topic": "description of the video theme",
        "story_count": 10
    }
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt
    )

    idea = json.loads(response.output_text)

    return idea

def generate_story_ideas(
    client,
    video_idea
    ):

    prompt = f"""
    We are creating this YouTube horror compilation:

    Title: {video_idea["title"]}
    Topic: {video_idea["topic"]}

    Generate exactly 20 DIFFERENT story concepts.

    The goal is to create a collection where every story feels
    like it came from a different person's life.

    REALISM:
    - Most stories should feel like something that could actually happen.
    - Prefer realistic or ambiguous explanations.
    - A few stories may have paranormal elements, but do not make
      every story supernatural.
    - Do not explain every mystery.
    - Simple disturbing situations are often scarier than elaborate plots.

    DIVERSITY:
    Across the 20 concepts, deliberately vary:

    - narrator age
    - narrator gender when relevant
    - occupation
    - location
    - living situation
    - time of day
    - source of the danger
    - type of strange event
    - whether the mystery is solved
    - whether another person is actually discovered
    - how the story ends

    Use a wide variety of situations such as:

    - strangers
    - neighbors
    - stalkers
    - unexplained noises
    - technology
    - cameras
    - phones
    - workplaces
    - apartments
    - houses
    - hotels
    - roads
    - vehicles
    - outdoor locations
    - deliveries
    - maintenance workers
    - roommates
    - mistaken assumptions
    - ambiguous paranormal events

    IMPORTANT:

    Do NOT repeatedly use:
    - someone secretly living inside a wall
    - someone living in an attic
    - someone living in a crawlspace
    - hidden mattresses
    - hidden notebooks
    - hidden photographs of the narrator
    - police discovering a squatter
    - secret passages
    - characters moving away at the end

    Across all 20 concepts, no more than TWO stories may involve
    someone secretly living inside or underneath a building.

    At least FIVE concepts should contain NO confirmed intruder.

    At least FIVE concepts should have completely realistic
    possible explanations.

    At least THREE concepts should take place somewhere other
    than the narrator's home.

    At least THREE concepts should involve technology in a
    meaningful way.

    At least TWO concepts should remain completely unresolved.

    At least TWO concepts should end with the narrator discovering
    an ordinary but disturbing explanation rather than something
    supernatural.

    Do not simply take the same story and change the location.

    Each concept should have a fundamentally different source
    of tension.

    Each premise should be 2-3 sentences.

    Do not write the full stories yet.
    Do not mention Reddit or AI.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "story_ideas",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "stories": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer"
                                    },
                                    "title": {
                                        "type": "string"
                                    },
                                    "premise": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "id",
                                    "title",
                                    "premise"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["stories"],
                    "additionalProperties": False
                }
            }
        }
    )

    story_ideas = json.loads(response.output_text)

    return story_ideas

def select_best_stories(client, video_idea, story_ideas):

    prompt = f"""
    You are selecting stories for this YouTube horror compilation:

    Title: {video_idea["title"]}
    Topic: {video_idea["topic"]}
    Number of stories needed: {video_idea["story_count"]}

    AVAILABLE STORY CONCEPTS:

    {json.dumps(story_ideas["stories"], indent=2)}

    Select exactly {video_idea["story_count"]} concepts.

    Your goal is NOT simply to choose the individually scariest stories.

    Your goal is to create the strongest COLLECTION of stories
    for one YouTube video.

    Every selected story should feel meaningfully different from
    the stories around it.

    PRIORITIZE:
    - strong suspense
    - believable situations
    - interesting hooks
    - stories that make viewers want to hear the ending
    - different sources of danger
    - different settings
    - different types of narrators
    - different types of endings
    - different levels of explanation

    THE FINAL COLLECTION SHOULD MIX:

    - realistic human threats
    - unexplained situations
    - ordinary situations that become disturbing
    - technology-related situations
    - stories outside the home
    - ambiguous situations
    - a small number of possibly paranormal stories

    IMPORTANT DIVERSITY RULES:

    - Do not select more than TWO stories involving someone
      secretly living inside a building.

    - Do not select more than TWO stories where the main threat
      is a stalker.

    - Do not select more than TWO strongly paranormal stories.

    - Include at least TWO stories where no intruder is discovered.

    - Include at least TWO stories that take place primarily
      somewhere other than the narrator's home.

    - Include at least ONE story involving technology in a
      meaningful way.

    - Include at least ONE story where the explanation turns out
      to be realistic but still disturbing.

    - Include at least ONE story where the central mystery
      remains unresolved.

    AVOID selecting multiple stories that share the same basic
    progression, even if their details are different.

    For example, avoid selecting several stories that all follow:

    strange noise
    -> investigation
    -> hidden room
    -> person discovered
    -> police arrive

    Think about how the stories will feel when heard one after another.

    The viewer should not be able to predict what kind of story
    comes next.

    Return ONLY the IDs of the selected stories.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "selected_stories",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "selected_ids": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        }
                    },
                    "required": ["selected_ids"],
                    "additionalProperties": False
                }
            }
        }
    )

    selection = json.loads(response.output_text)

    return selection["selected_ids"]

def get_replacement_story(
    client,
    video_idea,
    all_story_ideas,
    selected_stories,
    attempted_story_ids
):

    selected_ids = [
        story["id"]
        for story in selected_stories
    ]

    available_stories = [
        story
        for story in all_story_ideas
        if (
            story["id"] not in selected_ids
            and story["id"] not in attempted_story_ids
        )
    ]

    if not available_stories:
        return None

    prompt = f"""
    You are choosing a replacement story concept for this
    YouTube horror compilation.

    VIDEO:
    {video_idea["title"]}

    TOPIC:
    {video_idea["topic"]}

    CURRENTLY SELECTED STORIES:

    {json.dumps(selected_stories, indent=2)}

    AVAILABLE REPLACEMENTS:

    {json.dumps(available_stories, indent=2)}

    Choose the ONE replacement that would make the overall
    collection strongest.

    Prioritize a story that adds something the current collection
    does not already have.

    Consider:
    - setting
    - type of threat
    - source of tension
    - narrator situation
    - realistic vs unexplained events
    - technology
    - ending type
    - overall story structure

    Avoid choosing a replacement that feels too similar to
    another selected story.

    Also prioritize:
    - believable events
    - strong suspense
    - enough material for an 800-1100 word story
    - a concept that can escalate naturally

    Return ONLY the ID of the best replacement.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "replacement_story",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "replacement_id": {
                            "type": "integer"
                        }
                    },
                    "required": ["replacement_id"],
                    "additionalProperties": False
                }
            }
        }
    )

    result = json.loads(response.output_text)

    replacement_id = result["replacement_id"]

    for story in available_stories:

        if story["id"] == replacement_id:
            return story

    return None

def evaluate_premise(client, video_idea, story_idea):

    prompt = f"""
    You are checking a story premise before it is turned into a
    full horror story.

    VIDEO:
    {video_idea["title"]}

    TOPIC:
    {video_idea["topic"]}

    STORY TITLE:
    {story_idea["title"]}

    PREMISE:
    {story_idea["premise"]}

    Determine whether this premise can become a believable,
    internally consistent horror story.

    CHECK:

    LOGIC:
    - Can the events physically happen?
    - Does the timeline make sense?
    - Do locations and character movements make sense?
    - Does the premise contradict itself?

    REALISM:
    - Could this reasonably happen in the real world?
    - If technology, transportation, buildings, workplaces,
      police, or other real-world systems are involved, are they
      being used plausibly?
    - Does the premise require an unlikely coincidence?

    STORY POTENTIAL:
    - Is there enough material for an 800-1100 word story?
    - Is there a clear source of tension?
    - Can tension escalate naturally?
    - Does the premise have a believable direction?

    CLICHES:
    Check whether the premise relies too heavily on common
    AI horror patterns such as:
    - secret people living inside buildings
    - hidden rooms
    - crawlspaces
    - mysterious photographs
    - conveniently discovered notebooks
    - stalkers with no believable motivation
    - impossible technology
    - unexplained supernatural events in an otherwise realistic story

    IMPORTANT:

    Do NOT reject a premise simply because something strange or
    unexplained happens.

    A mystery can remain unresolved.

    The question is whether the EVENTS themselves can happen
    consistently within the rules of the story.

    PRACTICAL EVALUATION STANDARD:

    Evaluate the CORE PREMISE only.

    This is a short 2-4 sentence concept, NOT the finished story.

    Do NOT require the premise to already explain every:
    - technical detail
    - police procedure
    - company policy
    - legal response
    - platform feature
    - timestamp
    - camera angle
    - database
    - radio frequency
    - investigation step

    If a missing detail can easily be decided while writing the full
    story, it is NOT a premise problem.

    For example, do not fail a premise simply because:
    - the exact app or platform is unspecified
    - police response is not described
    - a technical mechanism needs a small clarification
    - character motivation can naturally be established in the story
    - the premise leaves some mystery unresolved

    ONLY flag a problem if it seriously threatens the core concept.

    Examples of real premise problems:
    - the central event is physically impossible
    - the premise directly contradicts itself
    - the timeline cannot work
    - the entire concept depends on impossible technology
    - the central character must behave absurdly for the plot to work
    - fixing the issue would require changing the core story

    Do not search for hypothetical problems.

    If the core concept works and remaining details can reasonably be
    decided during story writing, give it strong scores.

    Return no more than 3 problems.

    If there are no important premise-level problems, return an empty
    problems list.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "premise_evaluation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "logic": {
                            "type": "integer"
                        },
                        "realism": {
                            "type": "integer"
                        },
                        "story_potential": {
                            "type": "integer"
                        },
                        "problems": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [
                        "logic",
                        "realism",
                        "story_potential",
                        "problems"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    evaluation = json.loads(response.output_text)

    minimum_score = min(
        evaluation["logic"],
        evaluation["realism"],
        evaluation["story_potential"]
    )

    if minimum_score >= 7 and len(evaluation["problems"]) <= 3:
        evaluation["pass"] = True
    else:
        evaluation["pass"] = False

    return evaluation

def revise_premise(client, video_idea, story_idea, evaluation):

    problems_text = "\n".join(
        f"- {problem}"
        for problem in evaluation["problems"]
    )

    prompt = f"""
    You are repairing a story premise before it is turned into a
    full horror story.

    VIDEO:
    {video_idea["title"]}

    TOPIC:
    {video_idea["topic"]}

    STORY TITLE:
    {story_idea["title"]}

    CURRENT PREMISE:
    {story_idea["premise"]}

    PROBLEMS FOUND:
    {problems_text}

    Rewrite the premise to fix the identified problems.

    IMPORTANT:

    Preserve the core idea whenever possible.

    Do not replace the premise with a completely different story
    unless the original idea cannot logically work.

    LOGIC:
    - Make all events physically possible.
    - Make timing and movement consistent.
    - Make locations work realistically.
    - Remove contradictions.

    REALISM:
    - Use believable technology, transportation, buildings,
      workplaces, authorities, and character behavior.
    - Avoid convenient coincidences.
    - Give suspicious behavior a plausible opportunity or motive
      when necessary.

    STORY QUALITY:
    - Keep the central horror concept interesting.
    - Preserve the strongest part of the original idea.
    - Leave enough material for an 800-1100 word story.
    - Do not over-explain every detail.
    - Mystery and ambiguity are allowed.

    AVOID:
    - unnecessary supernatural explanations
    - adding hidden rooms or secret passages
    - adding someone secretly living inside a building
    - adding random stalkers without believable behavior
    - solving logic problems with coincidences

    Return ONLY the repaired premise.

    Keep it approximately 2-4 sentences.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt
    )

    revised_story_idea = story_idea.copy()

    revised_story_idea["premise"] = response.output_text.strip()

    return revised_story_idea

def prepare_premise(client, video_idea, story_idea):

    MAX_PREMISE_REVISIONS = 2

    current_story_idea = story_idea.copy()

    for attempt in range(MAX_PREMISE_REVISIONS + 1):

        print(
            f"\nCHECKING PREMISE: "
            f"{current_story_idea['title']}"
        )

        evaluation = evaluate_premise(
            client,
            video_idea,
            current_story_idea
        )

        print(
            "Premise scores:",
            f"Logic {evaluation['logic']}/10,",
            f"Realism {evaluation['realism']}/10,",
            f"Potential {evaluation['story_potential']}/10"
        )

        if evaluation["pass"]:

            print("PREMISE PASSED")

            return current_story_idea

        print("PREMISE FAILED")

        for problem in evaluation["problems"]:
            print("-", problem)

        if attempt < MAX_PREMISE_REVISIONS:

            print(
                f"REVISING PREMISE "
                f"({attempt + 1}/{MAX_PREMISE_REVISIONS})..."
            )

            current_story_idea = revise_premise(
                client,
                video_idea,
                current_story_idea,
                evaluation
            )

        else:

            print(
                "PREMISE STILL FAILED AFTER "
                "MAXIMUM REVISIONS"
            )

            return None

def generate_narrator_profile(client, video_idea, story_idea):

    prompt = f"""
    Create a believable narrator profile for this horror story.

    VIDEO:
    {video_idea["title"]}

    STORY:
    {story_idea["title"]}

    PREMISE:
    {story_idea["premise"]}

    The narrator should feel like a real person who could realistically
    experience the events in this premise.

    Choose characteristics that naturally fit the story.

    Vary things such as:
    - age
    - occupation
    - personality
    - speaking style
    - storytelling style

    The narrator should NOT automatically be:
    - highly observant
    - overly descriptive
    - philosophical
    - dramatic
    - a skilled storyteller

    Different people tell stories differently.

    Some people:
    - speak in short sentences
    - ramble slightly
    - focus on practical details
    - use casual language
    - barely describe their emotions
    - remember conversations clearly
    - forget exact details
    - explain too much
    - get straight to the point

    Make the profile appropriate for spoken first-person narration.

    Do not write the actual story.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "narrator_profile",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "age": {
                            "type": "integer"
                        },
                        "occupation": {
                            "type": "string"
                        },
                        "personality": {
                            "type": "string"
                        },
                        "speaking_style": {
                            "type": "string"
                        },
                        "storytelling_style": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "age",
                        "occupation",
                        "personality",
                        "speaking_style",
                        "storytelling_style"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    return json.loads(response.output_text)

def generate_full_story(
    client,
    video_idea,
    story_idea,
    narrator_profile
):

    prompt = f"""
    Write a full first-person horror story for a YouTube narration.

    VIDEO:
    {video_idea["title"]}

    STORY CONCEPT:
    Title: {story_idea["title"]}
    Premise: {story_idea["premise"]}

    NARRATOR PROFILE:

    Age: {narrator_profile["age"]}
    Occupation: {narrator_profile["occupation"]}
    Personality: {narrator_profile["personality"]}
    Speaking style: {narrator_profile["speaking_style"]}
    Storytelling style: {narrator_profile["storytelling_style"]}

    Write the story as THIS specific person.

    The narrator's vocabulary, sentence structure, amount of detail,
    dialogue, observations, and way of describing fear should naturally
    reflect this profile.

    Do not directly tell the audience the narrator's personality or
    storytelling style.

    Do not force the narrator to mention their age or occupation unless
    it naturally matters to the story.

    
    TARGET LENGTH:
    Approximately 800-1100 words.

    CORE STYLE:
    - Write like a normal person describing a disturbing experience
      that actually happened to them.
    - Use first person.
    - Use simple, natural, conversational English.
    - The narrator should NOT sound like a novelist.
    - The narrator should have a believable personality.
    - Use realistic everyday details when useful.
    - Dialogue should sound like something real people would say.
    - Keep sentences comfortable for spoken narration.
    - Build tension gradually.
    - Let the premise determine the structure of the story.

    PREMISE DISCIPLINE:

    The provided premise is the foundation of the story.

    Do NOT make the plot more complicated just to make it scarier.

    Do not introduce major new:
    - vehicles
    - attackers
    - accomplices
    - messages
    - photographs
    - livestreams
    - accounts
    - devices
    - locations
    - supernatural events
    - twists

    unless they are clearly necessary for the original premise.

    If the premise leaves a detail unspecified, choose the SIMPLEST
    believable explanation that allows the story to work.

    Every important event you add must have a clear cause.

    Every important object, message, photo, vehicle, or character that
    affects the climax must fit logically into the timeline.

    Do not introduce evidence that the story cannot later account for.

    Do not create a mystery simply by making technology behave in ways
    that real technology would not behave.

    If the story involves an app, phone, camera, vehicle, workplace,
    building, or other real-world system, keep its behavior simple and
    plausible.

    Prefer ONE coherent threat over several loosely connected threats.

    Before finishing the story, make sure:
    - the timeline is consistent
    - the same vehicle/person/device is not accidentally described
    in contradictory ways
    - photos or recordings have a plausible source
    - messages have a plausible sender or delivery mechanism
    - characters know only information they could realistically know
    
    REALISM:
    - Keep the story believable unless the premise specifically
      requires paranormal elements.
    - Do not add supernatural events just to make the ending scarier.
    - Characters should make reasonable decisions based on what
      they know at the time.
    - Do not make police, landlords, roommates, or other characters
      behave unrealistically just to advance the plot.
    - Coincidences should be rare.
    - Do not introduce unnecessary characters.
    - Do not over-explain the mystery.

    PACING:
    - Start with something that creates curiosity quickly.
    - Establish the situation without excessive background.
    - Introduce tension gradually.
    - Escalate naturally from the events in the premise.
    - Keep the strongest moment relatively late in the story.
    - After the main climax, finish relatively quickly.
    - Do not add several new twists after the climax.

    IMPORTANT:
    Do NOT force every story into the same structure.

    The story does NOT need to follow:
    strange noise
    -> investigation
    -> hidden space
    -> intruder
    -> police
    -> move away
    -> final creepy event

    Follow the natural structure suggested by THIS premise.

    OPENING VARIETY:

    Avoid automatically beginning with phrases such as:
    - "The first time I..."
    - "The first night..."
    - "At first I thought..."
    - "It started when..."
    - "I always thought..."

    Choose an opening appropriate to this specific story.

    Possible approaches include:
    - begin during an unsettling moment
    - begin with an ordinary routine
    - begin with dialogue
    - begin with an unusual discovery
    - begin with a specific memory
    - begin with a statement that raises a question
    - begin shortly before something goes wrong

    Do not use one of these mechanically.
    Choose what naturally fits the premise.

    AVOID AI-WRITING PATTERNS:

    Avoid:
    - excessive dramatic fragments
    - overly perfect foreshadowing
    - poetic descriptions of fear
    - philosophical reflections
    - repeated rhetorical questions
    - excessive use of em dashes
    - horror clichés
    - characters constantly saying how scared they are
    - suspicious objects conveniently appearing whenever
      the story needs another clue

    Avoid phrases and constructions such as:
    - "my blood ran cold"
    - "my stomach dropped" repeatedly
    - "I couldn't explain it"
    - "I wish I had..."
    - "little did I know"
    - "what happened next..."
    - "I still don't know..."
    - "all I know is..."
    - "to this day..."
    - "I never found out..."

    These phrases are not absolutely forbidden if natural,
    but do not use them as default horror-story shortcuts.

    CLUES:
    - Do not overload the story with creepy evidence.
    - Two or three strong details are better than ten convenient clues.
    - Every clue should make sense within the premise.
    - Do not automatically add hidden photographs, notebooks,
      children's shoes, drawings, fingerprints, or mattresses.
    - Do not automatically reveal someone secretly living nearby.

    POLICE AND AUTHORITIES:
    - Police do not need to appear in every story.
    - Do not automatically use police as the resolution.
    - If authorities naturally belong in the story, portray their
      involvement briefly and realistically.
    - The climax should not automatically be officers discovering
      the explanation.

    ENDING:
    The ending must fit THIS story.

    Possible ending types include:
    - completely resolved
    - partially resolved
    - unresolved
    - realistic explanation
    - disturbing realization
    - narrator simply leaving the situation
    - consequence of an earlier decision
    - discovery that changes how earlier events are understood
    - ambiguous final detail

    Do NOT automatically add another paranormal or creepy event
    after the main problem has already been resolved.

    Do NOT automatically end with the narrator saying they still
    hear, see, dream about, or think about the event.

    Do NOT force a final twist merely because this is horror.

    The ending should feel like where a real person would naturally
    stop telling the story.

    Do not mention Reddit.
    Do not mention AI.

    Return ONLY the finished story.
    Do not include the story title.
    Do not include commentary.
    """

    response = client.responses.create(
        model=STORY_MODEL,
        input=prompt
    )

    return response.output_text

def evaluate_story(client, video_idea, story_idea, story):

    prompt = f"""
    You are a strict quality-control editor for a YouTube horror
    narration channel.

    VIDEO:
    {video_idea["title"]}

    ORIGINAL PREMISE:
    {story_idea["premise"]}

    STORY:
    {story}

    Evaluate the story. Do NOT rewrite it.

    Check these categories:

    1. LOGIC
    - Do events physically and logically make sense?
    - Are there contradictions?
    - Does the explanation actually explain what happened?
    UNRESOLVED MYSTERIES:

    A horror story does NOT need to explain every mystery.

    Do not lower the logic or realism score merely because:
    - the narrator never identifies the sender
    - the antagonist's motive is unknown
    - the narrator does not learn how someone knew their location
    - police or security never solve the case
    - a strange event remains unexplained
    - the ending is ambiguous

    An unexplained event is acceptable if it is physically possible.

    For example:

    A stranger somehow knowing the narrator's location is NOT automatically
    a logic problem. They could be watching, following, using shared
    location data, know the narrator personally, or have another method
    the narrator never discovers.

    Only flag it as a logic problem if the story establishes facts that
    make the event impossible or contradictory.

    IMPORTANT:

    Distinguish between:

    UNEXPLAINED:
    "We never discovered how they knew where I was."
    This is allowed.

    IMPOSSIBLE:
    "The sender could not physically have known where I was based on facts
    already established by the story."
    This is a logic problem.

    Do not demand an explanation simply to close every mystery.
    2. REALISM
    - Do characters behave reasonably?
    - Are police, technology, transportation, workplaces, buildings,
      and other real-world elements believable?
    - Does anything feel conveniently engineered for the plot?

    3. NARRATOR VOICE
    - Does the narrator sound like a real person?
    - Does the narration sound overly polished or literary?
    - Does dialogue sound natural?

    4. PACING
    - Does tension build naturally?
    - Is there unnecessary repetition?
    - Does the story continue too long after the climax?

    5. AI WRITING PATTERNS
    Look for:
    - excessive one-line dramatic paragraphs
    - overly polished descriptions
    - horror clichés
    - unnecessary dramatic fragments
    - explaining emotions instead of letting events show them
    - repeated sentence structures

    6. ENDING
    - Does the ending feel natural?
    - Does it stop at the right point?
    - Does it unnecessarily explain the lesson or meaning?
    - Does it add an unnecessary final scare or reflection?

    Be strict.

    A story should PASS only if it is good enough to use in a
    finished YouTube video without another rewrite.

    Scores are from 1-10.

    Set "pass" to false if there is any significant logic,
    realism, writing, pacing, or ending problem.

    Keep each problem description short and specific.
    """

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "story_evaluation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "pass": {
                            "type": "boolean"
                        },
                        "logic": {
                            "type": "integer"
                        },
                        "realism": {
                            "type": "integer"
                        },
                        "voice": {
                            "type": "integer"
                        },
                        "pacing": {
                            "type": "integer"
                        },
                        "ending": {
                            "type": "integer"
                        },
                        "problems": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [
                        "pass",
                        "logic",
                        "realism",
                        "voice",
                        "pacing",
                        "ending",
                        "problems"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    return json.loads(response.output_text)

def revise_story(client, video_idea, story_idea, story, evaluation):

    problems_text = "\n".join(
        f"- {problem}"
        for problem in evaluation["problems"]
    )

    prompt = f"""
    You are revising a horror story for a YouTube narration channel.

    VIDEO:
    {video_idea["title"]}

    ORIGINAL PREMISE:
    {story_idea["premise"]}

    CURRENT STORY:
    {story}

    QUALITY-CONTROL PROBLEMS:
    {problems_text}

    Revise the story ONLY where necessary to fix the identified
    problems.

    REVISION PRIORITY:

    Fix logical and realism problems BEFORE improving style.

    If a problem involves:
    - contradictory vehicles
    - impossible timing
    - unexplained photos
    - unclear messages
    - unrealistic app behavior
    - unexplained character knowledge
    - unnecessary accomplices
    - conflicting locations
    - police or authority behavior

    then actually change the plot details needed to resolve that problem.

    Do NOT preserve a broken plot detail just because it was in the
    previous draft.

    Simplify when necessary.

    Prefer:
    - removing an unnecessary vehicle
    - removing an unnecessary photo
    - combining two characters into one
    - removing an extra twist
    - clarifying one believable technical mechanism
    - changing the timing of an event

    instead of adding more explanation on top of a broken setup.

    After revising, the story should have ONE clear version of what
    happened.

    Do not introduce new major plot elements while fixing old problems.

    IMPORTANT:

    Preserve what already works.

    Do not completely rewrite a good story just because a few
    sections need improvement.

    LOGIC:
    - Fix contradictions or events that do not physically make sense.
    - Make locations, transportation, technology, timing, and
      character actions believable.
    - Make sure the final explanation actually explains earlier events.

    REALISM:
    - Characters should behave reasonably.
    - Do not create convenient coincidences just to fix the plot.
    - Prefer simple believable explanations.

    NARRATOR VOICE:
    - Keep the narrator conversational and natural.
    - Do not make the prose more literary or polished.
    - Dialogue should sound like real conversation.

    AI WRITING PATTERNS:
    - Reduce unnecessary one-line dramatic paragraphs.
    - Remove clichés.
    - Remove overly polished descriptions.
    - Avoid repetitive sentence structures.
    - Do not repeatedly explain the narrator's emotions.

    ENDING:
    - End soon after the central event reaches its natural conclusion.
    - Do not explain the lesson, meaning, or theme.
    - Remove unnecessary reflection.
    - Do not add another scare merely to create a dramatic final line.

    LENGTH:
    Keep the finished story approximately 800-1100 words.

    Return ONLY the revised story.
    Do not explain your changes.
    """

    response = client.responses.create(
        model=STORY_MODEL,
        input=prompt
    )

    return response.output_text

def prepare_story(
    client,
    video_idea,
    story_idea,
    story
):

    MAX_STORY_REVISIONS = 1

    current_story = story

    for attempt in range(MAX_STORY_REVISIONS + 1):

        print(
            f"\nCHECKING STORY: "
            f"{story_idea['title']}"
        )

        evaluation = evaluate_story(
            client,
            video_idea,
            story_idea,
            current_story
        )

        minimum_score = min(
            evaluation["logic"],
            evaluation["realism"],
            evaluation["voice"],
            evaluation["pacing"],
            evaluation["ending"]
        )

        if (
            minimum_score >= 8
        ):
            evaluation["pass"] = True
        else:
            evaluation["pass"] = False

        print(
            "Story scores:",
            f"Logic {evaluation['logic']}/10,",
            f"Realism {evaluation['realism']}/10,",
            f"Voice {evaluation['voice']}/10,",
            f"Pacing {evaluation['pacing']}/10,",
            f"Ending {evaluation['ending']}/10"
        )

        if evaluation["pass"]:

            print("STORY PASSED")

            return current_story

        print("STORY FAILED")

        for problem in evaluation["problems"]:
            print("-", problem)

        if attempt < MAX_STORY_REVISIONS:

            print(
                f"REVISING STORY "
                f"({attempt + 1}/{MAX_STORY_REVISIONS})..."
            )

            current_story = revise_story(
                client,
                video_idea,
                story_idea,
                current_story,
                evaluation
            )

        else:

            print(
                "STORY STILL HAS ISSUES AFTER "
                "MAXIMUM REVISIONS"
            )

            return None











