"""Speaker catalogue for each supported language.

For Indic Parler TTS, ``speaker_name`` becomes part of the natural-language
voice description fed to the model. For HebTTS, ``speaker_name`` selects a
bundled reference WAV used as the zero-shot acoustic prompt — see
``tts/hebtts/_vendored/speakers/speakers.yaml``.
"""

from __future__ import annotations

from typing import TypedDict


class _SpeakerCatalogue(TypedDict):
    available: list[str]
    recommended: list[str]


LANGUAGE_SPEAKERS: dict[str, _SpeakerCatalogue] = {
    "as": {
        "available": ["Amit", "Sita", "Poonam", "Rakesh"],
        "recommended": ["Amit", "Sita"],
    },
    "bn": {
        "available": ["Arjun", "Aditi", "Tapan", "Rashmi", "Arnav", "Riya"],
        "recommended": ["Arjun", "Aditi"],
    },
    "brx": {
        "available": ["Bikram", "Maya", "Kalpana"],
        "recommended": ["Bikram", "Maya"],
    },
    "hne": {
        "available": ["Bhanu", "Champa"],
        "recommended": ["Bhanu", "Champa"],
    },
    "doi": {
        "available": ["Karan"],
        "recommended": ["Karan"],
    },
    "en": {
        "available": [
            "Thoma",
            "Mary",
            "Swapna",
            "Dinesh",
            "Meera",
            "Jatin",
            "Aakash",
            "Sneha",
            "Kabir",
            "Tisha",
            "Chingkhei",
            "Thoiba",
            "Priya",
            "Tarun",
            "Gauri",
            "Nisha",
            "Raghav",
            "Kavya",
            "Ravi",
            "Vikas",
            "Riya",
        ],
        "recommended": ["Thoma", "Mary"],
    },
    "gu": {
        "available": ["Yash", "Neha"],
        "recommended": ["Yash", "Neha"],
    },
    "hi": {
        "available": ["Rohit", "Divya", "Aman", "Rani"],
        "recommended": ["Rohit", "Divya"],
    },
    "kn": {
        "available": ["Suresh", "Anu", "Chetan", "Vidya"],
        "recommended": ["Suresh", "Anu"],
    },
    "ml": {
        "available": ["Anjali", "Anju", "Harish"],
        "recommended": ["Anjali", "Harish"],
    },
    "mni": {
        "available": ["Laishram", "Ranjit"],
        "recommended": ["Laishram", "Ranjit"],
    },
    "mr": {
        "available": ["Sanjay", "Sunita", "Nikhil", "Radha", "Varun", "Isha"],
        "recommended": ["Sanjay", "Sunita"],
    },
    "ne": {
        "available": ["Amrita"],
        "recommended": ["Amrita"],
    },
    "or": {
        "available": ["Manas", "Debjani"],
        "recommended": ["Manas", "Debjani"],
    },
    "pa": {
        "available": ["Divjot", "Gurpreet"],
        "recommended": ["Divjot", "Gurpreet"],
    },
    "sa": {
        "available": ["Aryan"],
        "recommended": ["Aryan"],
    },
    "ta": {
        "available": ["Kavitha", "Jaya"],
        "recommended": ["Jaya"],
    },
    "te": {
        "available": ["Prakash", "Lalitha", "Kiran"],
        "recommended": ["Prakash", "Lalitha"],
    },
    # Hebrew via HebTTS — names match speakers.yaml in the vendored
    # tree and the WAV files in tts/hebtts/_vendored/speakers/.
    "he": {
        "available": ["osim", "geek", "shaul"],
        "recommended": ["osim"],
    },
}


def get_speaker_description(language_code: str, speaker_name: str | None = None) -> str:
    """Build an Indic-Parler voice description.

    HebTTS does not consume text descriptions — engines that don't support
    them (currently only ``he``) must not call this function.
    """
    language_code = language_code.lower()

    if language_code not in LANGUAGE_SPEAKERS:
        raise ValueError(
            f"Unsupported language: {language_code}. "
            f"Available languages: {', '.join(LANGUAGE_SPEAKERS.keys())}"
        )

    if speaker_name is None:
        speaker_name = LANGUAGE_SPEAKERS[language_code]["recommended"][0]
    else:
        if speaker_name not in LANGUAGE_SPEAKERS[language_code]["available"]:
            raise ValueError(
                f"Speaker '{speaker_name}' not available for {language_code}. "
                f"Available speakers: {', '.join(LANGUAGE_SPEAKERS[language_code]['available'])}"
            )

    return (
        f"{speaker_name} speaks with a clear voice at a moderate speed and pitch. "
        f"The recording is of very high quality, with the speaker's voice sounding "
        f"clear and very close up."
    )
