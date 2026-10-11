# Hisham Khan 
# Start Date 2026-09-28
# Last update 2026-09-29
# Youtube Video Generator
"""
reddit-video-generator/
│
├── main.py
├── config.py
│
├── modules/
│   ├── idea_generator.py
│   ├── reddit_finder.py
│   ├── story_selector.py
│   ├── script_writer.py
│   ├── narrator.py
│   ├── visual_generator.py
│   ├── video_editor.py
│   └── file_manager.py
│
├── assets/
│   ├── music/
│   ├── fonts/
│   └── backgrounds/
│
└── output/
    └── 2026-09-28_10_scariest_reddit_stories/
        ├── stories/
        ├── scripts/
        ├── audio/
        ├── visuals/
        ├── metadata.json
        └── final_video.mp4
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import subprocess
import re
from difflib import SequenceMatcher

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)


#### These Functions Create and revise our video scripts >
def generate_idea():

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
        model="gpt-5-mini",
        input=prompt
    )

    idea = json.loads(response.output_text)

    return idea

def generate_story_ideas(video_idea):

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
        model="gpt-5-mini",
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

def select_best_stories(video_idea, story_ideas):

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
        model="gpt-5-mini",
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
        model="gpt-5-mini",
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

def evaluate_premise(video_idea, story_idea):

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
        model="gpt-5-mini",
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

def revise_premise(video_idea, story_idea, evaluation):

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
        model="gpt-5-mini",
        input=prompt
    )

    revised_story_idea = story_idea.copy()

    revised_story_idea["premise"] = response.output_text.strip()

    return revised_story_idea

def prepare_premise(video_idea, story_idea):

    MAX_PREMISE_REVISIONS = 2

    current_story_idea = story_idea.copy()

    for attempt in range(MAX_PREMISE_REVISIONS + 1):

        print(
            f"\nCHECKING PREMISE: "
            f"{current_story_idea['title']}"
        )

        evaluation = evaluate_premise(
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

def generate_narrator_profile(video_idea, story_idea):

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
        model="gpt-5-mini",
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
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text

def evaluate_story(video_idea, story_idea, story):

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
        model="gpt-5-mini",
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

def revise_story(video_idea, story_idea, story, evaluation):

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
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text

def prepare_story(
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

def review_story(video_idea, story_idea, story, previous_stories):

    previous_context = ""

    if previous_stories:
        previous_context = """
        PREVIOUS STORIES IN THIS VIDEO:

        The following stories have already been completed.
        Use them ONLY to identify repetition in structure, openings,
        endings, scares, settings, and writing patterns.

        Do not copy details from them.

        """

        for previous_story in previous_stories:
            previous_context += f"""
            ---
            {previous_story[:1500]}
            """

    else:
        previous_context = """
        This is the first story in the compilation.
        There are no previous stories to compare against.
        """

    prompt = f"""
    You are the final editor for a YouTube horror narration channel.

    VIDEO:
    {video_idea["title"]}

    ORIGINAL PREMISE:
    {story_idea["premise"]}

    CURRENT STORY:
    {story}

    {previous_context}

    Edit the CURRENT STORY into the strongest possible final version
    for spoken YouTube narration.

    CORE GOALS:
    - sound natural when spoken aloud
    - sound like a normal person telling a disturbing experience
    - preserve the core premise
    - maintain strong pacing
    - maintain realism when appropriate
    - remove obvious AI-writing patterns
    - make this story feel different from previous stories

    CHECK FOR REPETITION:

    Compare the current story with the previous stories.

    Look for repeated:
    - opening styles
    - sentence patterns
    - story structures
    - settings
    - clues
    - types of threats
    - police involvement
    - character behavior
    - climax structure
    - ending structure
    - final sentences

    If the current story feels structurally too similar to a previous
    story, revise it while preserving the original premise.

    OPENINGS:

    Avoid repeatedly beginning stories with:
    - "The first time..."
    - "The first night..."
    - "At first..."
    - "It started..."
    - narrator immediately explaining that they dismissed a strange noise

    If the opening resembles previous stories, rewrite it.

    NATURAL WRITING:

    Remove:
    - dialogue that sounds scripted
    - overly poetic language
    - philosophical reflections
    - excessive dramatic sentence fragments
    - horror clichés
    - unnecessary exposition
    - repetitive descriptions of fear
    - overly convenient clues
    - unnecessary characters
    - unrealistic character decisions

    Do not make the writing more literary.

    CLUES:

    Do not automatically use:
    - hidden photographs
    - notebooks
    - children's shoes
    - drawings
    - fingerprints
    - mattresses
    - secret rooms
    - crawlspaces
    - someone secretly living inside a building

    Only preserve these if they are genuinely important to the
    original premise.

    POLICE:

    Police should only appear if their involvement naturally makes
    sense.

    Do not automatically make police arrival the resolution or climax.

    ENDINGS:

    Check whether the ending resembles previous stories.

    Avoid repeatedly ending with:
    - "I still don't know..."
    - "I never found out..."
    - "All I know is..."
    - "To this day..."
    - the narrator still hearing the sound
    - the narrator still dreaming about the event
    - the same threat mysteriously returning
    - an unnecessary supernatural final twist
    - the narrator moving away and then experiencing one final scare

    A story is allowed to simply end once its central event has
    reached a satisfying conclusion.

    Do not add a twist solely because this is horror.
        Do not explain the meaning, theme, or lesson of the story
    to the audience.

    Avoid ending with several paragraphs of reflection.

    After the central event is resolved or reaches its final
    unexplained point, end the story relatively quickly.

    The narrator does not need to explain why the experience
    was scary. Let the events speak for themselves.

    Avoid philosophical closing statements or sentences that
    sound written specifically to create a dramatic final line.

    Prefer a simple, natural ending that sounds like where a
    real person would stop telling the story.
    
    PACING:

    Keep the strongest moment relatively late.

    Keep the aftermath concise.

    Do not continue escalating after the natural climax.

    LENGTH:

    Keep the final story approximately 800-1100 words.

    IMPORTANT:

    Previous stories are provided only as comparison material.

    Do NOT merge their plots, characters, locations, or details into
    the current story.

    Edit ONLY the current story.

    Return ONLY the final edited story.
    Do not explain your changes.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text

def save_video_info(
    output_folder,
    video_idea,
    selected_stories,
    all_story_ideas,
    attempted_story_ids=None,
    narrator_profiles=None
):

    if attempted_story_ids is None:
        attempted_story_ids = set()
        
    if narrator_profiles is None:
        narrator_profiles = {}
        
        
    video_info = {
        "video_idea": video_idea,
        "selected_stories": selected_stories,
        "all_story_ideas": all_story_ideas,
        "attempted_story_ids": list(attempted_story_ids),
        "narrator_profiles": narrator_profiles
    }

    file_path = os.path.join(
        output_folder,
        "video_info.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            video_info,
            file,
            indent=2
        )

def load_video_info(output_folder):

    file_path = os.path.join(
        output_folder,
        "video_info.json"
    )

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        video_info = json.load(file)

    return video_info

def get_completed_stories(
    project_folder,
    selected_stories
):

    completed_stories = []

    for number, story in enumerate(
        selected_stories,
        start=1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        if os.path.exists(story_file):
            completed_stories.append(
                story
            )

    return completed_stories

def generate_youtube_metadata(
    video_idea,
    selected_stories
):

    story_titles = []
    story_count = len(selected_stories)
    for story in selected_stories:

        if isinstance(story, dict):
            story_titles.append(
                story.get("title", "")
            )

    stories_text = "\n".join(
        f"- {title}"
        for title in story_titles
        if title
    )

    prompt = f"""
Create YouTube metadata for an original fictional horror story compilation.

ACTUAL COMPLETED STORY COUNT:
{story_count}

IMPORTANT:
Use this completed story count in the title and description.
If the original video idea mentions a different number,
ignore that number.

VIDEO IDEA:
{video_idea}

STORIES:
{stories_text}

Return ONLY valid JSON in this exact format:

{{
    "title": "YouTube title here",
    "description": "YouTube description here"
}}

TITLE RULES:
- Maximum 100 characters
- Make it clickable but not ridiculous clickbait
- Horror/scary-story niche
- Natural human wording
- Do not say Reddit because these stories are original fiction
- Prefer a strong searchable phrase like Scary Stories, Horror Stories, Late Night Stories, etc.

DESCRIPTION RULES:
- 2-4 short paragraphs
- Explain what the viewer is getting
- Mention that the stories are original fictional horror stories
- Keep it natural
- Do not reveal endings
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    metadata = json.loads(
        response.output_text
    )

    return metadata

def save_youtube_metadata(
    project_folder,
    metadata
):

    metadata_file = os.path.join(
        project_folder,
        "youtube_metadata.json"
    )

    with open(
        metadata_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"YOUTUBE METADATA SAVED: {metadata_file}"
    )



#### These Functions Create and revise our video scripts <
#--------------------------------------------------------------
#### These Functions Create and Narrations



def split_story_for_tts(text, max_chars=9000):

    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        if len(current_chunk) + len(paragraph) + 2 <= max_chars:
            current_chunk += paragraph + "\n\n"

        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            current_chunk = paragraph + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def generate_story_audio(
    story_file_path,
    audio_file_path,
    voice_id="JBFqnCBsd6RMkjVDRZzb"
):

    if os.path.exists(audio_file_path):
        print(f"AUDIO ALREADY EXISTS - SKIPPING: {audio_file_path}")
        return

    with open(story_file_path, "r", encoding="utf-8") as f:
        story_text = f.read()
    
    story_text = story_text.replace("**", "")
    story_text = story_text.replace("__", "")
    story_text = story_text.replace("`", "")

    chunks = split_story_for_tts(story_text)

    print(f"\nGENERATING AUDIO: {story_file_path}")
    print(f"Chunks: {len(chunks)}")

    with open(audio_file_path, "wb") as output_file:

        for index, chunk in enumerate(chunks, start=1):

            print(
                f"Generating audio chunk "
                f"{index}/{len(chunks)}..."
            )

            audio = elevenlabs.text_to_speech.convert(
                voice_id=voice_id,
                text=chunk,
                model_id="eleven_flash_v2_5",
                output_format="mp3_44100_128"
            )

            for audio_chunk in audio:
                if audio_chunk:
                    output_file.write(audio_chunk)

    print(f"AUDIO SAVED: {audio_file_path}")

def generate_all_story_audio(
    project_folder,
    story_count
):

    audio_folder = os.path.join(
        project_folder,
        "audio"
    )

    os.makedirs(
        audio_folder,
        exist_ok=True
    )

    for number in range(1, story_count + 1):

        story_file_path = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        audio_file_path = os.path.join(
            audio_folder,
            f"story_{number:02d}.mp3"
        )

        if not os.path.exists(story_file_path):
            print(
                f"STORY {number} HAS NO FINAL FILE - SKIPPING AUDIO"
            )
            continue

        generate_story_audio(
            story_file_path,
            audio_file_path
        )


#### These Functions Create and Narrations


#### These Functions create the video 


def create_ffmpeg_test_video(audio_file, output_file):

    command = [
        "ffmpeg",
        "-y",

        "-f", "lavfi",
        "-i", "color=c=black:s=1920x1080:r=30",

        "-i", audio_file,

        "-t", "10",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",
        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(f"TEST VIDEO SAVED: {output_file}")

def split_story_into_visual_scenes(
    story_text,
    target_words=110
):

    sentences = re.split(
        r'(?<=[.!?])\s+',
        story_text.strip()
    )

    scenes = []
    current_scene = []
    current_word_count = 0

    for sentence in sentences:

        sentence_word_count = len(
            sentence.split()
        )

        if (
            current_scene
            and current_word_count + sentence_word_count > target_words
        ):

            scenes.append(
                " ".join(current_scene)
            )

            current_scene = []
            current_word_count = 0

        current_scene.append(sentence)

        current_word_count += sentence_word_count

    if current_scene:
        scenes.append(
            " ".join(current_scene)
        )

    return scenes

def generate_visual_plan(
    video_idea,
    story_idea,
    story_text,
    narrator_profile
):

    narration_scenes = split_story_into_visual_scenes(
        story_text
    )

    numbered_scenes = []

    for number, scene in enumerate(
        narration_scenes,
        start=1
    ):
        numbered_scenes.append({
            "scene_number": number,
            "narration": scene
        })

    prompt = f"""
    You are creating the visual plan for a YouTube horror story.

    VIDEO:
    {video_idea["title"]}

    STORY:
    {story_idea["title"]}

    NARRATOR PROFILE:
    {json.dumps(narrator_profile, indent=2)}

    NARRATION SCENES:
    {json.dumps(numbered_scenes, indent=2)}

    Create exactly ONE visual prompt for every narration scene.

    The visuals should feel cinematic, realistic, dark, atmospheric,
    and suitable for a horror-story YouTube video.

    IMPORTANT:

        STRICT STORY GROUNDING:

    - Every visual must be directly supported by the narration for that scene.
    - Do NOT invent actions, locations, vehicles, objects, injuries,
      characters, or events that are not present in the narration.
    - Do NOT move the narrator into a car, building, room, or other
      location unless that scene clearly places them there.
    - Do NOT change who owns an object or vehicle.
    - Do NOT imply that an item was lost, abandoned, stolen, or left behind
      unless the narration explicitly says so.
    - If a scene is reflective or does not contain a strong visual event,
      use a simple environment or character reaction that is already
      supported by the story.

    VISUAL VARIETY:

    - Do not create two nearly identical visuals for nearby scenes.
    - If two scenes cover the same event, use a different perspective,
      detail shot, object, environment, or reaction rather than repeating
      the same wide shot.
    - Avoid repeating the same phone-looking composition several times.
    - Keep recurring characters visually consistent.
    - Keep recurring locations consistent.
    - Match the visual to what is happening in that narration section.
    - Do not invent major events that are not in the story.
    - Prefer believable environments and people.
    - Avoid excessive gore.
    - Avoid supernatural imagery unless the story actually requires it.
    - Do not put readable text inside generated images.
    - Do not rely on phone screens containing exact readable messages.
    - If a phone is important, show the person reacting to the phone
      or show the device from an angle where exact text is not needed.
    - Avoid making every image a close-up face.
    - Vary camera angles and compositions.
    - Some scenes may focus on environments, objects, vehicles,
      buildings, weather, or other details instead of people.
    - Use 16:9 cinematic compositions.
    - Each prompt should describe only ONE clear image.

    Each visual prompt should clearly describe:

    - main subject
    - environment
    - important objects
    - time of day
    - lighting
    - camera framing
    - mood

    Return one result for every provided scene.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "visual_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {
                                        "type": "integer"
                                    },
                                    "visual_prompt": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "scene_number",
                                    "visual_prompt"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["scenes"],
                    "additionalProperties": False
                }
            }
        }
    )

    visual_plan = json.loads(
        response.output_text
    )

    return visual_plan

def create_story_video(
    background_file,
    audio_file,
    output_file
):

    command = [
        "ffmpeg",
        "-y",

        # Loop the background forever
        "-stream_loop", "-1",
        "-i", background_file,

        # Narration
        "-i", audio_file,

        # Use only background video + narration audio
        "-map", "0:v:0",
        "-map", "1:a:0",

        # Make every background fit YouTube 1080p
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080",

        "-r", "30",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        # Stop when narration ends
        "-shortest",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"STORY VIDEO SAVED: {output_file}"
    )

def generate_all_story_videos(
    project_folder,
    story_count,
    background_file
):

    video_folder = os.path.join(
        project_folder,
        "videos"
    )

    os.makedirs(
        video_folder,
        exist_ok=True
    )

    for number in range(1, story_count + 1):

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        output_file = os.path.join(
            video_folder,
            f"story_{number:02d}_video.mp4"
        )

        if not os.path.exists(audio_file):
            print(
                f"STORY {number} HAS NO AUDIO - SKIPPING VIDEO"
            )
            continue

        if os.path.exists(output_file):
            print(
                f"VIDEO ALREADY EXISTS - SKIPPING: {output_file}"
            )
            continue

        create_story_video(
            background_file,
            audio_file,
            output_file
        )

def generate_subtitles(
    audio_file,
    story_file,
    subtitle_file
):

    if os.path.exists(subtitle_file):
        print(
            f"SUBTITLES ALREADY EXIST - SKIPPING: {subtitle_file}"
        )
        return

    print(
        f"\nGENERATING SUBTITLES: {audio_file}"
    )

    with open(
        story_file,
        "r",
        encoding="utf-8"
    ) as f:
        story_text = f.read()

    with open(audio_file, "rb") as audio:

        raw_srt = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="srt",
            language="en"
        )

    subtitle_blocks = parse_srt(
        raw_srt
    )

    corrected_blocks = correct_subtitle_text(
        story_text,
        subtitle_blocks
    )

    final_srt = build_corrected_srt(
        subtitle_blocks,
        corrected_blocks
    )

    with open(
        subtitle_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(final_srt)

    print(
        f"SUBTITLES SAVED: {subtitle_file}"
    )

def parse_srt(srt_text):

    blocks = []

    raw_blocks = srt_text.strip().split("\n\n")

    for raw_block in raw_blocks:

        lines = raw_block.strip().splitlines()

        if len(lines) < 3:
            continue

        number = int(lines[0])

        timestamps = lines[1]

        text = " ".join(lines[2:])

        blocks.append({
            "number": number,
            "timestamps": timestamps,
            "text": text
        })

    return blocks

def correct_subtitle_text(
    story_text,
    subtitle_blocks
):

    clean_story = story_text.replace("**", "")
    clean_story = clean_story.replace("__", "")
    clean_story = clean_story.replace("`", "")

    whisper_blocks = [
        {
            "number": block["number"],
            "text": block["text"]
        }
        for block in subtitle_blocks
    ]

    prompt = f"""
    You are correcting subtitles for a narrated YouTube story.

    ORIGINAL STORY:
    {clean_story}

    WHISPER SUBTITLE BLOCKS:
    {json.dumps(whisper_blocks, indent=2)}

    The original story is the SOURCE OF TRUTH.

    Whisper was used only to estimate timing and may contain:
    - spelling errors
    - punctuation errors
    - incorrect names
    - incorrect speaker attribution
    - missing words
    - slightly changed wording

    Correct the subtitle text using the original story.

    IMPORTANT:

    - Return exactly the same number of subtitle blocks.
    - Keep every block number unchanged.
    - Preserve the original story's wording as closely as possible.
    - Preserve the original order of the narration.
    - Do not summarize.
    - Do not paraphrase.
    - Do not invent words.
    - Use the Whisper text only to determine approximately
      which original words belong in each subtitle block.
    - Do not include timestamps.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "corrected_subtitles",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "blocks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "number": {
                                        "type": "integer"
                                    },
                                    "text": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "number",
                                    "text"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["blocks"],
                    "additionalProperties": False
                }
            }
        }
    )

    result = json.loads(
        response.output_text
    )

    return result["blocks"]

def build_corrected_srt(
    original_blocks,
    corrected_blocks
):

    corrected_by_number = {
        block["number"]: block["text"]
        for block in corrected_blocks
    }

    srt_parts = []

    for block in original_blocks:

        number = block["number"]

        corrected_text = corrected_by_number.get(
            number,
            block["text"]
        )

        srt_parts.append(
            f"{number}\n"
            f"{block['timestamps']}\n"
            f"{corrected_text}"
        )

    return "\n\n".join(srt_parts)

def get_word_timestamps(audio_file):

    print(
        f"\nGETTING WORD TIMESTAMPS: {audio_file}"
    )

    with open(audio_file, "rb") as audio:

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="verbose_json",
            timestamp_granularities=["word"],
            language="en"
        )

    return transcription.words

def normalize_subtitle_word(word):

    return re.sub(
        r"[^a-z0-9]",
        "",
        word.lower()
    )

def get_story_words(story_text):

    clean_story = story_text.replace("**", "")
    clean_story = clean_story.replace("__", "")
    clean_story = clean_story.replace("`", "")

    raw_words = re.findall(
        r"\S+",
        clean_story
    )

    story_words = []

    for word in raw_words:

        normalized = normalize_subtitle_word(
            word
        )

        if not normalized:
            continue

        story_words.append({
            "text": word,
            "normalized": normalized
        })

    return story_words

def get_whisper_words(timestamp_words):

    whisper_words = []

    for word in timestamp_words:

        normalized = normalize_subtitle_word(
            word.word
        )

        if not normalized:
            continue

        whisper_words.append({
            "text": word.word,
            "normalized": normalized,
            "start": word.start,
            "end": word.end
        })

    return whisper_words

def align_story_words(
    story_words,
    whisper_words
):

    story_normalized = [
        word["normalized"]
        for word in story_words
    ]

    whisper_normalized = [
        word["normalized"]
        for word in whisper_words
    ]

    matcher = SequenceMatcher(
        None,
        story_normalized,
        whisper_normalized,
        autojunk=False
    )

    matches = {}

    for block in matcher.get_matching_blocks():

        for offset in range(block.size):

            story_index = block.a + offset
            whisper_index = block.b + offset

            matches[story_index] = whisper_index

    return matches

def assign_story_timestamps(
    story_words,
    whisper_words,
    matches
):

    timed_words = []

    matched_story_indexes = sorted(
        matches.keys()
    )

    for story_index, story_word in enumerate(story_words):

        # Exact match found
        if story_index in matches:

            whisper_index = matches[story_index]

            timed_words.append({
                "text": story_word["text"],
                "start": float(
                    whisper_words[whisper_index]["start"]
                ),
                "end": float(
                    whisper_words[whisper_index]["end"]
                )
            })

            continue

        # Find closest matched word before this word
        previous_matches = [
            index
            for index in matched_story_indexes
            if index < story_index
        ]

        # Find closest matched word after this word
        next_matches = [
            index
            for index in matched_story_indexes
            if index > story_index
        ]

        previous_index = (
            previous_matches[-1]
            if previous_matches
            else None
        )

        next_index = (
            next_matches[0]
            if next_matches
            else None
        )

        # Unmatched word is between two known words
        if (
            previous_index is not None
            and next_index is not None
        ):

            previous_whisper = matches[
                previous_index
            ]

            next_whisper = matches[
                next_index
            ]

            gap_start = float(
                whisper_words[
                    previous_whisper
                ]["end"]
            )

            gap_end = float(
                whisper_words[
                    next_whisper
                ]["start"]
            )

            words_in_gap = (
                next_index
                - previous_index
                - 1
            )

            position = (
                story_index
                - previous_index
                - 1
            )

            duration = (
                gap_end - gap_start
            ) / words_in_gap

            start = (
                gap_start
                + duration * position
            )

            end = start + duration

        else:
            start = None
            end = None

        timed_words.append({
            "text": story_word["text"],
            "start": start,
            "end": end
        })

    return timed_words

def create_subtitle_blocks(
    timed_words,
    max_words=8,
    max_chars=45,
    max_duration=3.5,
    min_duration=1.2
):

    blocks = []
    current_words = []

    for word in timed_words:

        if (
            word["start"] is None
            or word["end"] is None
        ):
            continue

        current_words.append(word)

        text = " ".join(
            item["text"]
            for item in current_words
        )

        start = current_words[0]["start"]
        end = current_words[-1]["end"]

        duration = end - start

        ends_sentence = bool(
            re.search(
                r'[.!?]["\']?$',
                word["text"]
            )
        )

        should_finish = (
            duration >= max_duration
            or (
                duration >= min_duration
                and (
                    len(current_words) >= max_words
                    or len(text) >= max_chars
                    or (
                        ends_sentence
                        and len(current_words) >= 4
                    )
                )
            )
        )

        if should_finish:

            blocks.append({
                "start": start,
                "end": end,
                "text": text
            })

            current_words = []

    if current_words:

        blocks.append({
            "start": current_words[0]["start"],
            "end": current_words[-1]["end"],
            "text": " ".join(
                item["text"]
                for item in current_words
            )
        })

    return blocks

def format_srt_timestamp(seconds):

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    secs = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )

def build_srt_from_blocks(
    subtitle_blocks
):

    srt_parts = []

    for index, block in enumerate(
        subtitle_blocks,
        start=1
    ):

        start_time = format_srt_timestamp(
            block["start"]
        )

        end_time = format_srt_timestamp(
            block["end"]
        )

        srt_parts.append(
            f"{index}\n"
            f"{start_time} --> {end_time}\n"
            f"{block['text']}"
        )

    return "\n\n".join(srt_parts)

def generate_word_timed_subtitles(
    story_file,
    audio_file,
    subtitle_file
):

    if os.path.exists(subtitle_file):
        print(
            f"SUBTITLES ALREADY EXIST - SKIPPING: {subtitle_file}"
        )
        return

    print(
        f"\nGENERATING WORD-TIMED SUBTITLES: {audio_file}"
    )

    with open(
        story_file,
        "r",
        encoding="utf-8"
    ) as f:
        story_text = f.read()

    timestamp_words = get_word_timestamps(
        audio_file
    )

    story_words = get_story_words(
        story_text
    )

    whisper_words = get_whisper_words(
        timestamp_words
    )

    matches = align_story_words(
        story_words,
        whisper_words
    )

    match_rate = (
        len(matches)
        / len(story_words)
        * 100
    )

    print(
        f"SUBTITLE MATCH RATE: "
        f"{match_rate:.2f}%"
    )

    timed_words = assign_story_timestamps(
        story_words,
        whisper_words,
        matches
    )

    subtitle_blocks = create_subtitle_blocks(
        timed_words
    )

    final_srt = build_srt_from_blocks(
        subtitle_blocks
    )

    with open(
        subtitle_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(final_srt)

    print(
        f"SUBTITLES SAVED: {subtitle_file}"
    )

def generate_all_story_subtitles(
    project_folder,
    story_count
):

    subtitle_folder = os.path.join(
        project_folder,
        "subtitles"
    )

    os.makedirs(
        subtitle_folder,
        exist_ok=True
    )

    for number in range(
        1,
        story_count + 1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        subtitle_file = os.path.join(
            subtitle_folder,
            f"story_{number:02d}.srt"
        )

        if not os.path.exists(story_file):
            print(
                f"STORY {number} HAS NO FINAL TEXT "
                f"- SKIPPING SUBTITLES"
            )
            continue

        if not os.path.exists(audio_file):
            print(
                f"STORY {number} HAS NO AUDIO "
                f"- SKIPPING SUBTITLES"
            )
            continue

        generate_word_timed_subtitles(
            story_file,
            audio_file,
            subtitle_file
        )

def create_subtitled_video(
    video_file,
    subtitle_file,
    output_file
):

    subtitle_path = os.path.abspath(
        subtitle_file
    )

    subtitle_path = subtitle_path.replace(
        "\\",
        "/"
    )

    subtitle_path = subtitle_path.replace(
        ":",
        "\\:"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-vf",
        (
            f"subtitles='{subtitle_path}':"
            "force_style='"
            "FontName=Arial,"
            "FontSize=22,"
            "Alignment=2,"
            "MarginV=55,"
            "Outline=2,"
            "Shadow=1"
            "'"
        ),

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "copy",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"SUBTITLED VIDEO SAVED: {output_file}"
    )

def create_subtitle_preview(
    video_file,
    subtitle_file,
    output_file
):

    subtitle_path = os.path.abspath(
        subtitle_file
    )

    subtitle_path = subtitle_path.replace(
        "\\",
        "/"
    )

    subtitle_path = subtitle_path.replace(
        ":",
        "\\:"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-t", "20",

        "-vf",
        (
            f"subtitles='{subtitle_path}':"
            "force_style='"
            "FontName=Arial,"
            "FontSize=22,"
            "Alignment=2,"
            "MarginV=55,"
            "Outline=2,"
            "Shadow=1"
            "'"
        ),

        "-c:v", "libx264",
        "-preset", "veryfast",

        "-c:a", "copy",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"SUBTITLE PREVIEW SAVED: {output_file}"
    )

def generate_all_subtitled_videos(
    project_folder,
    story_count
):

    output_folder = os.path.join(
        project_folder,
        "subtitled_videos"
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    for number in range(
        1,
        story_count + 1
    ):

        video_file = os.path.join(
            project_folder,
            "videos",
            f"story_{number:02d}_video.mp4"
        )

        subtitle_file = os.path.join(
            project_folder,
            "subtitles",
            f"story_{number:02d}.srt"
        )

        output_file = os.path.join(
            output_folder,
            f"story_{number:02d}_subtitled.mp4"
        )

        if not os.path.exists(video_file):
            print(
                f"STORY {number} HAS NO VIDEO "
                f"- SKIPPING"
            )
            continue

        if not os.path.exists(subtitle_file):
            print(
                f"STORY {number} HAS NO SUBTITLES "
                f"- SKIPPING"
            )
            continue

        if os.path.exists(output_file):
            print(
                f"SUBTITLED VIDEO ALREADY EXISTS "
                f"- SKIPPING: {output_file}"
            )
            continue

        create_subtitled_video(
            video_file,
            subtitle_file,
            output_file
        )

def create_concat_file(
    video_files,
    concat_file
):

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for video_file in video_files:

            absolute_path = os.path.abspath(
                video_file
            )

            absolute_path = absolute_path.replace(
                "\\",
                "/"
            )

            f.write(
                f"file '{absolute_path}'\n"
            )

def combine_story_videos(
    video_files,
    output_file,
    concat_file
):

    create_concat_file(
        video_files,
        concat_file
    )

    command = [
        "ffmpeg",
        "-y",

        "-f", "concat",
        "-safe", "0",

        "-i", concat_file,

        "-c", "copy",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"FINAL VIDEO SAVED: {output_file}"
    )

def get_subtitled_story_files(
    project_folder,
    story_count
):

    video_files = []

    for number in range(
        1,
        story_count + 1
    ):

        video_file = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{number:02d}_subtitled.mp4"
        )

        if os.path.exists(video_file):
            video_files.append(
                video_file
            )

    return video_files

def add_background_ambience(
    video_file,
    music_file,
    output_file
):

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-stream_loop", "-1",
        "-i", music_file,

        "-filter_complex",
        (
            "[1:a]volume=0.025[ambience];"
            "[0:a][ambience]amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2[audio]"
        ),

        "-map", "0:v",
        "-map", "[audio]",

        "-c:v", "copy",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"VIDEO WITH AMBIENCE SAVED: {output_file}"
    )

def escape_drawtext_text(text):

    text = text.replace("\\", "\\\\")
    text = text.replace(":", r"\:")
    text = text.replace("'", r"\'")

    return text

def create_story_transition(
    story_number,
    story_title,
    output_file,
    duration=3
):

    number_text = escape_drawtext_text(
        f"STORY {story_number}"
    )

    title_text = escape_drawtext_text(
        story_title.upper()
    )

    command = [
        "ffmpeg",
        "-y",

        "-f", "lavfi",
        "-i",
        f"color=c=black:s=1920x1080:r=30:d={duration}",

        "-f", "lavfi",
        "-i",
        f"anullsrc=r=44100:cl=mono:d={duration}",

        "-vf",
        (
            "drawtext="
            "fontfile='C\\:/Windows/Fonts/arial.ttf':"
            f"text='{number_text}':"
            "fontcolor=white:"
            "fontsize=38:"
            "x=(w-text_w)/2:"
            "y=(h/2)-90,"
            "drawtext="
            "fontfile='C\\:/Windows/Fonts/arial.ttf':"
            f"text='{title_text}':"
            "fontcolor=white:"
            "fontsize=56:"
            "x=(w-text_w)/2:"
            "y=(h/2)-10"
        ),

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"TRANSITION SAVED: {output_file}"
    )

def generate_all_story_transitions(
    project_folder,
    selected_stories
):

    transition_folder = os.path.join(
        project_folder,
        "transitions"
    )

    os.makedirs(
        transition_folder,
        exist_ok=True
    )

    for number, story in enumerate(
        selected_stories,
        start=1
    ):

        if number == 1:
            continue

        story_video = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{number:02d}_subtitled.mp4"
        )

        if not os.path.exists(story_video):
            print(
                f"STORY {number} HAS NO VIDEO "
                f"- SKIPPING TRANSITION"
            )
            continue

        transition_file = os.path.join(
            transition_folder,
            f"story_{number:02d}_transition.mp4"
        )

        if os.path.exists(transition_file):
            print(
                f"TRANSITION ALREADY EXISTS "
                f"- SKIPPING: {transition_file}"
            )
            continue

        create_story_transition(
            number,
            story["title"],
            transition_file
        )

def get_video_files_with_transitions(
    project_folder,
    story_count
):

    video_files = []

    for number in range(
        1,
        story_count + 1
    ):

        story_video = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{number:02d}_subtitled.mp4"
        )

        if not os.path.exists(story_video):
            continue

        if number > 1:

            transition_file = os.path.join(
                project_folder,
                "transitions",
                f"story_{number:02d}_transition.mp4"
            )

            if os.path.exists(transition_file):
                video_files.append(
                    transition_file
                )

        video_files.append(
            story_video
        )

    return video_files






#### These Functions create the video


project_folder = os.path.join(
    "output",
    "10_late-night_messages_you_never_want_to_hear__scary_stories_of_calls_texts__voicemails"
)

video_info = load_video_info(
    project_folder
)

completed_stories = get_completed_stories(
    project_folder,
    video_info["selected_stories"]
)

metadata = generate_youtube_metadata(
    video_info["video_idea"],
    completed_stories
)

save_youtube_metadata(
    project_folder,
    metadata
)

print("\nCOMPLETED STORIES:")
print(len(completed_stories))

print("\nGENERATED YOUTUBE METADATA")

print("\nTITLE:")
print(metadata["title"])

print("\nDESCRIPTION:")
print(metadata["description"])






print("\nYOUTUBE VIDEO GENERATOR")

print("\n1. Create new video")
print("2. Resume existing video")

choice = input("\nChoose an option: ")


# -----------------------------------
# CREATE NEW VIDEO
# -----------------------------------

if choice == "1":

    print("\nCREATING NEW VIDEO...")

    idea = generate_idea()

    print("\nVIDEO IDEA:")
    print(idea)

    story_ideas = generate_story_ideas(idea)

    print("\nGENERATED STORY IDEAS:")
    for story in story_ideas["stories"]:
        print(
            story["id"],
            "-",
            story["title"]
        )

    selected_ids = select_best_stories(
        idea,
        story_ideas
    )

    selected_stories = [
        story
        for story in story_ideas["stories"]
        if story["id"] in selected_ids
    ]
    
    all_story_ideas = story_ideas["stories"]

    attempted_story_ids = set()
    narrator_profiles = {}
    
    print("\nSELECTED STORIES:")
    for story in selected_stories:
        print(
            story["id"],
            "-",
            story["title"]
        )


    # Create folder name from video title

    folder_name = idea["title"].lower()

    folder_name = "".join(
        char if char.isalnum() or char in " _-" else ""
        for char in folder_name
    )

    folder_name = folder_name.replace(" ", "_")

    output_folder = os.path.join(
        "output",
        folder_name
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )


    # Save project information

    save_video_info(
        output_folder,
        idea,
        selected_stories,
        all_story_ideas
    )

    print(
        f"\nPROJECT SAVED: {output_folder}"
    )


# -----------------------------------
# RESUME EXISTING VIDEO
# -----------------------------------

elif choice == "2":

    print("\nRESUME VIDEO")

    folder_name = input(
        "Enter the project folder name: "
    )

    output_folder = os.path.join(
        "output",
        folder_name
    )

    video_info = load_video_info(
        output_folder
    )

    if video_info is None:

        print("\nProject not found.")
        print("Check the folder name and try again.")

        exit()

    idea = video_info["video_idea"]

    selected_stories = video_info["selected_stories"]

    all_story_ideas = video_info.get(
    "all_story_ideas",
    selected_stories)
    
    attempted_story_ids = set(
    video_info.get(
        "attempted_story_ids",
        []
        )   
    )
    
    narrator_profiles = video_info.get(
    "narrator_profiles",
    {}
    )   
    
    print("\nPROJECT LOADED:")
    print(idea["title"])

    print(
        f"Stories planned: {len(selected_stories)}"
    )


# -----------------------------------
# INVALID OPTION
# -----------------------------------

else:

    print("\nInvalid option.")
    exit()


# # Generate, review, and save every selected story

previous_stories = []

for number, story_idea in enumerate(selected_stories, start=1):

    file_name = f"story_{number:02d}.txt"
    draft_file_name = f"story_{number:02d}_draft.txt"

    file_path = os.path.join(
        output_folder,
        file_name
    )

    draft_file_path = os.path.join(
        output_folder,
        draft_file_name
    )

    # -----------------------------------
    # FINAL STORY ALREADY EXISTS
    # -----------------------------------

    if os.path.exists(file_path):

        print(
            f"\nSTORY {number} ALREADY EXISTS - SKIPPING"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            existing_story = file.read()

        previous_stories.append(existing_story)
        
        attempted_story_ids.add(
        story_idea["id"]
        )
        
        continue


# -----------------------------------
# CHECK / REPAIR PREMISE
# -----------------------------------

    print(
        f"\nPREPARING STORY "
        f"{number}/{len(selected_stories)}"
    )

    current_story_idea = story_idea


    while True:

        attempted_story_ids.add(
            current_story_idea["id"]
        )

        save_video_info(
            output_folder,
            idea,
            selected_stories,
            all_story_ideas,
            attempted_story_ids,
            narrator_profiles
        )

        prepared_story_idea = prepare_premise(
            idea,
            current_story_idea
        )

        if prepared_story_idea is not None:

            break

        print(
            f"\nPREMISE FAILED: "
            f"{current_story_idea['title']}"
        )

        replacement = get_replacement_story(
            idea,
            all_story_ideas,
            selected_stories,
            attempted_story_ids
            )

        if replacement is None:

            print(
                "\nNO REPLACEMENT PREMISES AVAILABLE"
            )

            prepared_story_idea = None

            break

        print(
            f"\nTRYING REPLACEMENT: "
            f"{replacement['title']}"
        )

        current_story_idea = replacement


    if prepared_story_idea is None:

        print(
            f"\nCOULD NOT COMPLETE STORY {number}"
        )

        continue
    
    selected_stories[number - 1] = prepared_story_idea

    save_video_info(
        output_folder,
        idea,
        selected_stories,
        all_story_ideas,
        attempted_story_ids,
        narrator_profiles
    )

    # -----------------------------------
    # LOAD OR GENERATE DRAFT
    # -----------------------------------

    profile_key = str(number)

    if profile_key in narrator_profiles:

        narrator_profile = narrator_profiles[
            profile_key
        ]

        print("\nUSING SAVED NARRATOR PROFILE:")
        print(narrator_profile)

    else:

        narrator_profile = generate_narrator_profile(
            idea,
            prepared_story_idea
        )

        narrator_profiles[
            profile_key
        ] = narrator_profile

        save_video_info(
            output_folder,
            idea,
            selected_stories,
            all_story_ideas,
            attempted_story_ids,
            narrator_profiles
        )

        print("\nNEW NARRATOR PROFILE:")
        print(narrator_profile)
    
    if os.path.exists(draft_file_path):

        print(
            f"\nDRAFT FOR STORY {number} "
            f"ALREADY EXISTS - LOADING"
        )

        with open(
            draft_file_path,
            "r",
            encoding="utf-8"
        ) as file:
            draft = file.read()

    else:

        print(
            f"\nGENERATING STORY "
            f"{number}/{len(selected_stories)}"
        )

        print(
            prepared_story_idea["title"]
        )


        draft = generate_full_story(
            idea,
            prepared_story_idea,
            narrator_profile
        )

        with open(
            draft_file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(draft)

        print(
            f"SAVED DRAFT: "
            f"{draft_file_path}"
        )


    # -----------------------------------
    # QUALITY CONTROL
    # -----------------------------------

    print(
        f"\nQUALITY CHECKING STORY {number}..."
    )

    final_story = prepare_story(
        idea,
        prepared_story_idea,
        draft
    )
    
    if final_story is None:

        print(
            f"\nSTORY {number} FAILED QUALITY CONTROL"
        )

        if os.path.exists(draft_file_path):
            os.remove(draft_file_path)

        continue


    # -----------------------------------
    # SAVE FINAL STORY
    # -----------------------------------

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(final_story)

    previous_stories.append(final_story)

    print(
        f"SAVED FINAL STORY: "
        f"{file_path}"
    )


print("\nALL AVAILABLE STORIES COMPLETE!")

generate_all_story_audio(
    output_folder,
    len(selected_stories)
)